"""
AI服务层
实现智能总结生成和合同顾问问答功能
支持DeepSeek API和自部署模型
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI
import re

from app.models.contract import Contract
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment
from app.models.ai_summary import AISummary
from app.core.config import settings
from app.core.redis_client import redis_client


class ComplianceAIError(Exception):
    """AI 服务一般错误（网络异常、模型 API 错误响应等）"""
    pass


class ComplianceAIInvalidResponseError(Exception):
    """AI 返回内容无法解析为合法 JSON 结构（两次重试均失败）"""
    pass


class AIService:
    """AI服务类"""
    
    def __init__(self):
        # 初始化OpenAI兼容客户端
        # max_retries=0：禁用 SDK 内置重试，由上层 for attempt in range(2) 控制
        # timeout=300：单次请求最长等待 5 分钟
        self.client = AsyncOpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_API_BASE,
            timeout=settings.AI_TIMEOUT,
            max_retries=0,
        )
        self.model = settings.AI_MODEL
    
    async def generate_summary(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> Optional[AISummary]:
        """
        生成AI智能总结
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            AI总结对象
        """
        try:
            # 1. 检查缓存
            cache_key = f"ai:summary:{contract_id}"
            cached_summary = await redis_client.get(cache_key)
            
            if cached_summary:
                # 从数据库获取完整对象
                query = select(AISummary).where(AISummary.contract_id == contract_id)
                result = await db.execute(query)
                return result.scalar_one_or_none()
            
            # 2. 获取合同和评审信息
            contract_query = select(Contract).where(Contract.id == contract_id)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
            
            if not contract:
                return None
            
            reviews_query = select(Review).where(Review.contract_id == contract_id)
            reviews_result = await db.execute(reviews_query)
            reviews = reviews_result.scalars().all()
            
            # 3. 计算审批进度
            total_count = len(reviews)
            completed_count = sum(1 for r in reviews if r.status == "approved")
            approval_status = "completed" if completed_count == total_count else "in_progress"
            
            # 4. 提取关键问题
            key_issues = await self._extract_key_issues(reviews, db)
            
            # 5. 保存或更新总结
            summary_query = select(AISummary).where(AISummary.contract_id == contract_id)
            summary_result = await db.execute(summary_query)
            summary = summary_result.scalar_one_or_none()
            
            if summary:
                summary.approval_status = approval_status
                summary.completed_count = completed_count
                summary.total_count = total_count
                summary.review_count = len([r for r in reviews if r.opinion])
                summary.key_issues = key_issues
            else:
                summary = AISummary(
                    contract_id=contract_id,
                    approval_status=approval_status,
                    completed_count=completed_count,
                    total_count=total_count,
                    review_count=len([r for r in reviews if r.opinion]),
                    key_issues=key_issues
                )
                db.add(summary)
            
            await db.commit()
            await db.refresh(summary)
            
            # 6. 缓存结果(30分钟 = 1800秒)
            await redis_client.set(cache_key, "1", expire=1800)
            
            return summary
            
        except Exception as e:
            print(f"生成AI总结失败: {str(e)}")
            return None
    
    async def _extract_key_issues(
        self,
        reviews: List[Review],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        提取关键问题
        包含"建议"、"需要"、"问题"、"风险"、"隐患"关键词的意见
        
        Args:
            reviews: 评审记录列表
            db: 数据库会话
            
        Returns:
            关键问题列表(最多3个)
        """
        from app.models.comment import Comment
        
        key_issues = []
        keywords = ["建议", "需要", "问题", "风险", "隐患"]
        
        for review in reviews:
            if not review.opinion:
                continue
            
            # 检查是否包含关键词
            has_keyword = any(keyword in review.opinion for keyword in keywords)
            
            if has_keyword:
                # 获取该评审的所有评论(回复)
                comments_query = select(Comment).where(
                    Comment.review_id == review.id
                ).order_by(Comment.created_at.desc())
                comments_result = await db.execute(comments_query)
                comments = comments_result.scalars().all()
                
                # 提取解决方案(如果有回复)
                solution = None
                if comments:
                    # 取最新的回复作为解决方案
                    latest_comment = comments[0]
                    solution = latest_comment.content
                
                key_issues.append({
                    "issue": review.opinion,
                    "reviewer": review.role,
                    "solution": solution
                })
                
                # 最多返回3个关键问题
                if len(key_issues) >= 3:
                    break
        
        return key_issues
    
    async def answer_question(
        self,
        contract_id: str,
        question: str,
        current_user_id: str,
        db: AsyncSession
    ) -> str:
        """
        AI合同顾问问答
    
        优先级：
        1. 关键词命中 → 纯 DB 直查（快速、零成本）
        2. 关键词未命中 → 调 DeepSeek 大模型（带合同上下文）
    
        Args:
            contract_id: 合同ID
            question: 用户问题
            current_user_id: 当前用户ID
            db: 数据库会话
    
        Returns:
            答案字符串
        """
        try:
            # 1. 获取合同和评审信息
            contract_query = select(Contract).where(Contract.id == contract_id)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
    
            if not contract:
                return "合同不存在"
    
            reviews_query = select(Review).where(Review.contract_id == contract_id)
            reviews_result = await db.execute(reviews_query)
            reviews = reviews_result.scalars().all()
    
            # 2. 关键词分支（DB 直查，快速返回）
            question_lower = question.lower()
    
            # 评审总结 → 调用大模型
            if any(k in question for k in ["总结", "汇总", "评审进度", "评审情况", "进度吗"]):
                return await self._ai_summary(
                    contract=contract,
                    reviews=list(reviews),
                    db=db,
                )
    
            # 法务意见查询
            if "法务" in question:
                legal_reviews = [r for r in reviews if "法务" in r.role and r.opinion]
                if legal_reviews:
                    opinions = "\n".join([
                        f"- {r.role}: {r.opinion}"
                        for r in legal_reviews
                    ])
                    return f"法务意见如下:\n{opinions}"
                else:
                    return "暂无法务意见"
    
            # 风险项查询
            if "风险" in question or "未确认" in question:
                pending_reviews = [r for r in reviews if r.status == "reviewing"]
                if pending_reviews:
                    items = "\n".join([
                        f"- {r.role} ({r.step}): {r.opinion or '待评审'}"
                        for r in pending_reviews
                    ])
                    return f"当前风险项/未确认项:\n{items}"
                else:
                    return "所有评审项已确认,无风险项"
    
            # 待办任务查询
            if "待我处理" in question or "待办" in question:
                user_pending_reviews = [
                    r for r in reviews
                    if r.status == "pending" and str(r.reviewer_id) == str(current_user_id)
                ]
                if user_pending_reviews:
                    items = "\n".join([
                        f"- {r.role} ({r.step})"
                        for r in user_pending_reviews
                    ])
                    return f"您有 {len(user_pending_reviews)} 个待处理评审项:\n{items}"
                else:
                    return "您当前没有待处理的评审任务"
    
            # 3. 兜底：调用大模型（带合同完整上下文）
            context = await self._build_contract_context(
                contract=contract,
                reviews=list(reviews),
                db=db,
            )
            return await self._ask_llm(question=question, context=context)
    
        except Exception as e:
            print(f"AI问答失败: {str(e)}")
            return "抱歉,处理您的问题时出现错误,请稍后重试"
    
    # ------------------------------------------------------------------
    #  大模型相关：上下文组装 + LLM 调用
    # ------------------------------------------------------------------

    async def _build_contract_context(
        self,
        contract: Contract,
        reviews: list,
        db: AsyncSession,
    ) -> str:
        """
        组装合同的完整上下文，喂给大模型。

        包含：合同信息 + 评审人列表（姓名/角色/状态/意见） + 全部评论（作者/内容）
        """
        from app.models.user import User as UserModel

        sections: list[str] = []

        # ---- 1. 合同基本信息 ----
        sections.append(f"## 合同信息")
        sections.append(f"名称：{contract.name}")
        if contract.description:
            sections.append(f"描述：{contract.description}")
        sections.append("")

        # ---- 2. 评审人状态 ----
        sorted_reviews = sorted(
            reviews,
            key=lambda r: (r.step if r.step is not None else 9999, r.created_at or 0),
        )
        sections.append(f"## 评审进度（共 {len(sorted_reviews)} 位评审人）")
        for r in sorted_reviews:
            name = r.reviewer.name if r.reviewer else "未知用户"
            status_text = "已通过" if r.status == ReviewStatus.APPROVED else "待审批"
            opinion_text = r.opinion.strip() if r.opinion else "（未发表意见）"
            sections.append(f"- [review-{r.id}] {name}（{r.role}）：{status_text} | 意见：{opinion_text}")
        sections.append("")

        # ---- 3. 全部评论 ----
        comments_query = select(Comment).where(
            Comment.contract_id == str(contract.id)
        ).order_by(Comment.created_at.asc())
        comments_result = await db.execute(comments_query)
        all_comments = list(comments_result.scalars().all())

        if all_comments:
            # 批量查作者名
            author_ids = list({str(c.author_id) for c in all_comments})
            user_query = select(UserModel).where(UserModel.id.in_(author_ids))
            user_result = await db.execute(user_query)
            user_map = {str(u.id): u.name for u in user_result.scalars().all()}

            sections.append(f"## 评论记录（共 {len(all_comments)} 条）")
            for c in all_comments:
                author_name = user_map.get(str(c.author_id), "未知用户")
                # 标记是否为回复
                reply_to = ""
                if c.parent_comment_id:
                    reply_to = " [回复]"
                if c.review_id:
                    # 找到对应评审人的角色
                    parent_review = next(
                        (r for r in sorted_reviews if str(r.id) == str(c.review_id)),
                        None,
                    )
                    if parent_review:
                        pr_name = parent_review.reviewer.name if parent_review.reviewer else ""
                        reply_to = f" [评审-{pr_name}下评论]"
                sections.append(f"- [comment-{c.id}] {author_name}{reply_to}：{c.content or ''}")
            sections.append("")
        else:
            sections.append("## 评论记录\n暂无评论。\n")

        return "\n".join(sections)

    async def _ai_summary(
        self,
        contract: Contract,
        reviews: list,
        db: AsyncSession,
    ) -> str:
        """调用大模型，基于全部评审和评论内容生成简洁的三段式总结"""
        # 1. 构建完整上下文
        context = await self._build_contract_context(
            contract=contract,
            reviews=reviews,
            db=db,
        )

        # 2. 定制 system prompt
        system_prompt = (
            "你是「AI 合同预审助理」，负责对合同评审进度做简洁总结。\n\n"
            "输出格式严格如下，不要加多余标题或分隔线：\n\n"
            "⚠️ 当前风险/问题\n"
            "  逐条列出当前存在的风险和未解决的问题，指明是谁提出的、是否已有应对措施。\n\n"
            "👤 责任归属人\n"
            "  列出每个待处理事项对应的责任人（姓名+角色）及当前状态。\n\n"
            "📋 具体推进事项\n"
            "  列出接下来需要推进的具体事项，明确谁需要做什么。\n\n"
            "**引用规则（必须遵守）**：\n"
            "1. 只有在明确引用**某条评审意见的具体内容**时，才使用 [ref:review-{review_id}] 标记。\n"
            "2. 只有在明确引用**某条评论的具体内容**时，才使用 [ref:comment-{comment_id}] 标记。\n"
            "3. **对于尚未发表意见的评审人**（意见为「未发表意见」状态的），不要添加任何引用标记。\n"
            "4. 当一句话涉及多条引用时，可添加多个 [ref:...] 标记。\n"
            "5. 当一句话无具体引用来源时，不追加标记。\n"
            "6. {review_id} 与 {comment_id} 必须使用上下文中 [review-xxx] 或 [comment-xxx] 形式给出的实际 ID，禁止杜撰。\n"
            "7. 标记格式：[ref:review-xxx] / [ref:comment-xxx]，不要加空格、不要加引号。\n\n"
            "其他规则：\n"
            "1. 内容务必简洁，每条不超过两句话。\n"
            "2. 使用评审人和评论者的真实姓名。\n"
            "3. 如果风险已有应对措施，说明措施内容；未解决的标注「未解决」。\n"
            "4. 不要复述原文，要提炼核心意思。\n"
            "5. 总字数控制在 600 字以内（不含 [ref:...] 标记）。"
        )

        user_prompt = (
            f"以下是当前合同的完整评审上下文：\n\n"
            f"{context}\n\n"
            f"---\n"
            f"请基于以上内容，按指定格式总结当前评审的风险、责任人和推进事项。"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                temperature=0.3,
            )
            answer = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            if finish_reason == 'length':
                print(f"[WARNING] AI总结被截断(finish_reason=length, max_tokens=4096)，建议增大max_tokens")
            if not answer or not answer.strip():
                print(f"AI总结返回内容为空, finish_reason={finish_reason}")
                return await self._summarize_progress_and_opinions(
                    contract_id=str(contract.id),
                    reviews=reviews,
                    db=db,
                )
            # 验证引用标记，移除无法匹配的引用
            answer = await self._validate_refs(answer, context)
            return answer.strip()
        except Exception as e:
            print(f"AI总结调用失败: {str(e)}")
            # 降级：回退到 DB 直查
            try:
                return await self._summarize_progress_and_opinions(
                    contract_id=str(contract.id),
                    reviews=reviews,
                    db=db,
                )
            except Exception as e2:
                print(f"DB直查总结也失败: {str(e2)}")
                # 最后兜底：完全不依赖 DB 的纯文本总结
                return self._build_fallback_summary(reviews)

    async def _ask_llm(self, question: str, context: str) -> str:
        """
        调用 DeepSeek 大模型回答问题。

        System prompt 严格约束：只回答评审进度和评论中的问题，拒绝其他内容。
        """
        system_prompt = (
            "你是「AI 合同预审助理」，专门帮助用户了解合同评审进度和评论中的问题。\n\n"
            "规则：\n"
            "1. 你只能回答关于当前合同评审进度、评审人状态、评论中的问题和意见相关的内容。\n"
            "2. 如果用户问的是与合同评审无关的问题，礼貌地告知你只能回答评审相关的问题。\n"
            "3. 回答要简洁明了，重点突出，使用中文。\n"
            "4. 引用评审人或评论者时，请使用他们的真实姓名。\n"
            "5. 如果评论中有具体问题或风险，请明确指出并说明是谁提出的。"
            "\n\n**引用规则**：当你在回答中引用某条评审意见或评论时，在引用句子之后追加结构化标记：[ref:review-{id}] 或 [ref:comment-{id}]，ID 必须严格使用上下文中给出的真实 ID。"
        )

        user_prompt = (
            f"以下是当前合同的完整评审上下文：\n\n"
            f"{context}\n\n"
            f"---\n"
            f"用户问题：{question}\n\n"
            f"请基于以上上下文回答用户的问题。如果上下文中没有足够信息，请如实说明。"
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                temperature=0.3,  # 低温度，减少幻觉
            )
            answer = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            if finish_reason == 'length':
                print(f"[WARNING] LLM回答被截断(finish_reason=length, max_tokens=2048)，建议增大max_tokens")
            if not answer or not answer.strip():
                print(f"LLM回答返回内容为空, finish_reason={finish_reason}")
                return "抱歉，未能生成回答。"
            # 验证引用标记，移除无法匹配的引用
            answer = await self._validate_refs(answer, context)
            return answer.strip()
        except Exception as e:
            print(f"LLM调用失败: {str(e)}")
            return "抱歉，AI服务暂时不可用，请稍后重试。"

    async def _validate_refs(self, response: str, context: str) -> str:
        """
        验证 AI 响应中的 [ref:...] 标记，移除无法匹配上下文中实际 ID 的引用。
        防止 AI 幻觉产生不存在的引用导致前端显示「引用不可用」。
        """
        # 从上下文中提取所有有效 ID
        valid_review_ids = set(re.findall(r'\[review-([^\]]+)\]', context))
        valid_comment_ids = set(re.findall(r'\[comment-([^\]]+)\]', context))

        def _replace_invalid(match):
            ref_type = match.group(1)  # 'review' 或 'comment'
            ref_id = match.group(2)
            if ref_type == 'review' and ref_id in valid_review_ids:
                return match.group(0)
            if ref_type == 'comment' and ref_id in valid_comment_ids:
                return match.group(0)
            print(f"移除无效引用: [ref:{ref_type}-{ref_id}]")
            return ''

        response = re.sub(r'\[ref:(review|comment)-([^\]]+)\]', _replace_invalid, response)

        # 移除不完整的引用标记（被截断的 [ref:... 缺少关闭的 ]）
        # 例如：末尾被截断的 [ref:review-981de641-feef-4434-9e6f-c
        response = re.sub(r'\[ref:(?:review|comment)-[^\]]*$', '', response)

        return response

    def _build_fallback_summary(self, reviews: list) -> str:
        """完全不依赖 DB 的纯文本兜底总结"""
        from app.models.review import ReviewStatus

        approved = [r for r in reviews if r.status == ReviewStatus.APPROVED]
        pending = [r for r in reviews if r.status != ReviewStatus.APPROVED]

        lines: list[str] = []
        lines.append("⚠️ 当前风险/问题")
        if pending:
            for r in pending:
                name = r.reviewer.name if r.reviewer else "未知用户"
                lines.append(f"  • {name}（{r.role}）尚未审批")
        else:
            lines.append("  暂无明显风险")

        lines.append("")
        lines.append("👤 责任归属人")
        if pending:
            for r in pending:
                name = r.reviewer.name if r.reviewer else "未知用户"
                status_text = "待审批" if r.status == ReviewStatus.PENDING else "审核中"
                lines.append(f"  • {name}（{r.role}）— {status_text}")
        elif approved:
            lines.append("  所有评审人已通过")
        else:
            lines.append("  暂未配置评审人")

        lines.append("")
        lines.append("📋 具体推进事项")
        if pending:
            for r in pending:
                name = r.reviewer.name if r.reviewer else "未知用户"
                lines.append(f"  • {name}（{r.role}）需完成审批")
        elif approved:
            lines.append("  ✅ 全部评审已通过")
        else:
            lines.append("  暂无具体推进事项")

        return "\n".join(lines)

    async def _summarize_progress_and_opinions(
        self,
        contract_id: str,
        reviews: list,
        db: AsyncSession,
    ) -> str:
        """构造简洁的三段式评审总结：风险/问题 → 责任归属人 → 推进事项"""
        # 拉取该合同的全部评论
        comments_query = select(Comment).where(Comment.contract_id == contract_id)
        comments_result = await db.execute(comments_query)
        all_comments = list(comments_result.scalars().all())

        # 按 review_id 分组评论
        comments_by_review: dict[str, list] = {}
        top_level_comments: list = []
        for c in all_comments:
            if c.review_id:
                comments_by_review.setdefault(str(c.review_id), []).append(c)
            elif not c.parent_comment_id:
                top_level_comments.append(c)

        # 按 step 排序
        sorted_reviews = sorted(
            reviews,
            key=lambda r: (r.step if r.step is not None else 9999, r.created_at or 0),
        )
        total = len(sorted_reviews)
        approved = [r for r in sorted_reviews if r.status == ReviewStatus.APPROVED]
        pending = [r for r in sorted_reviews if r.status != ReviewStatus.APPROVED]

        lines: list[str] = []

        # ---- 一、当前风险/问题 ----
        risk_keywords = ["问题", "风险", "建议", "需要", "隐患", "修改", "补充",
                         "缺失", "错误", "不符", "纠正", "不当", "注意"]
        risk_items: list[str] = []

        for r in sorted_reviews:
            name = r.reviewer.name if r.reviewer else "未知用户"
            # 待审批本身就是风险
            if r.status != ReviewStatus.APPROVED:
                risk_items.append(f"{name}（{r.role}）尚未审批")
            # 从评审意见中提取风险点
            if r.opinion and r.opinion.strip():
                opinion_text = r.opinion.strip()
                if any(kw in opinion_text for kw in risk_keywords):
                    # 截取关键句，避免过长
                    short = opinion_text
                    if len(short) > 50:
                        short = short[:50] + "..."
                    risk_items.append(f"{name}：{short}")
            # 从评审下的评论中提取风险
            for c in comments_by_review.get(str(r.id), []):
                content = (c.content or "").strip()
                if content and any(kw in content for kw in risk_keywords):
                    author_name = c.author.name if c.author else ""
                    if len(content) > 50:
                        content = content[:50] + "..."
                    risk_items.append(f"{author_name}：{content}")

        # 从顶层评论中提取风险（只取评论中含风险的，最多3条）
        risk_from_comments = 0
        for c in top_level_comments:
            if risk_from_comments >= 3:
                break
            content = (c.content or "").strip()
            if content and any(kw in content for kw in risk_keywords):
                author_name = c.author.name if c.author else ""
                if len(content) > 50:
                    content = content[:50] + "..."
                risk_items.append(f"{author_name}：{content}")
                risk_from_comments += 1

        lines.append("⚠️ 当前风险/问题")
        if risk_items:
            for i, item in enumerate(risk_items[:5], 1):  # 最多5条
                lines.append(f"  {i}. {item}")
        else:
            lines.append("  暂无明显风险")

        # ---- 二、责任归属人 ----
        lines.append("")
        lines.append("👤 责任归属人")
        if pending:
            for r in pending:
                name = r.reviewer.name if r.reviewer else "未知用户"
                status_desc = "待审批" if r.status == ReviewStatus.PENDING else "审核中"
                opinion_hint = ""
                if r.opinion and r.opinion.strip():
                    opinion_hint = "，已提出意见"
                lines.append(f"  • {name}（{r.role}）— {status_desc}{opinion_hint}")
        else:
            if approved:
                lines.append("  所有评审人已通过")
            else:
                lines.append("  暂未配置评审人")

        # ---- 三、具体推进事项 ----
        lines.append("")
        lines.append("📋 具体推进事项")
        action_items: list[str] = []
        idx = 1

        for r in pending:
            name = r.reviewer.name if r.reviewer else "未知用户"
            if r.status == ReviewStatus.PENDING and not r.opinion:
                action_items.append(f"{name}（{r.role}）需完成审批")
            elif r.opinion and r.opinion.strip():
                # 已有意见但未通过，需给出结论
                action_items.append(f"{name}（{r.role}）需给出审批结论")
            else:
                action_items.append(f"{name}（{r.role}）需完成审批")

        # 从评论中提取待办（最多2条）
        action_from_comments = 0
        for c in top_level_comments:
            if action_from_comments >= 2:
                break
            content = (c.content or "").strip()
            author_name = c.author.name if c.author else ""
            action_keywords = ["申请", "需要", "请", "要求", "待确认", "待处理"]
            if any(kw in content for kw in action_keywords) and len(content) > 5:
                short = content
                if len(short) > 40:
                    short = short[:40] + "..."
                action_items.append(f"跟进{author_name}：{short}")
                action_from_comments += 1

        if action_items:
            for i, item in enumerate(action_items[:5], 1):  # 最多5条
                lines.append(f"  {i}. {item}")
        else:
            if total > 0 and not pending:
                lines.append("  ✅ 全部评审已通过，可进入下一阶段")
            else:
                lines.append("  暂无具体推进事项")

        return "\n".join(lines)
    
    # ──────────────────────────────────────────────────────────────────
    #  合规检查 (Requirement 3 + 4)
    # ──────────────────────────────────────────────────────────────────

    _COMPLIANCE_SYSTEM_PROMPT = """你是「合同合规检查助理」。请基于「合同规范」「合同文件正文」「字段初稿」三类输入，
逐条比对并产出合规检查结果。

【输入】
1. 规则集合（每条规则给出 id / rule_type / title / requirement / severity）：
   - rule_type ∈ {number, name, description, file}
     · number → 规则作用于「合同编号字段初稿」
     · name → 规则作用于「合同名称字段初稿」+ 合同正文
     · description → 规则作用于「合同描述字段初稿」+ 合同正文
     · file → 规则作用于「合同文件正文」
   - severity ∈ {must, should}
2. 合同文件正文（extracted_contract_text，可能是 null 表示无文本）
3. 文件是否被截断（text_truncated）
4. 三个字段初稿：number_draft / name_draft / description_draft（可能为 null）

【输出严格 JSON】（只输出 JSON，不要任何前后说明）：
{
  "violations": [
    {
      "rule_id": "<必须为输入规则集合中的实际 id>",
      "location": "<必须与该 rule_id 对应规则的 rule_type 完全一致>",
      "excerpt": "<不超过 500 字符，location=number/name/description 时取自字段初稿；location=file 时取自 extracted_contract_text 相关片段；允许为空字符串>",
      "description": "<不超过 500 字符，具体说明违反点>",
      "suggestion": "<不超过 500 字符，给出修改建议>",
      "severity": "<必须与对应规则 severity 完全一致，must 或 should>"
    }
  ],
  "suggested_name": "<1-200 字符，符合规范的合同名称>",
  "suggested_description": "<0-2000 字符，符合规范的合同描述，允许空字符串>"
}

【约束】
- 不要输出 suggested_number 字段（合同编号由系统发号器生成）
- 不要输出 compliance_score 字段（由后端基于 violations 与 severity 计算，LLM 不参与打分）
- 当某 rule_type=number/name/description 对应的字段初稿为 null 或空字符串，
  不要为该字段类型输出 violation，仅 rule_type=file 不受字段初稿影响
- 必须使用规则的真实 id，不要杜撰
- text_truncated=true 时，可在 description 中提示「正文被截断，可能影响判断」"""

    async def check_compliance(
        self,
        *,
        rules: list,
        extracted_text: str,
        text_truncated: bool,
        number_draft: Optional[str],
        name_draft: Optional[str],
        description_draft: Optional[str],
    ) -> dict:
        """
        执行合规检查。

        Args:
            rules: ComplianceRule 对象列表（或含 id/rule_type/severity/title/requirement 的 dict 列表）
            extracted_text: 从合同文件抽取的纯文本
            text_truncated: 文本是否被截断
            number_draft: 合同编号初稿（可为 None）
            name_draft: 合同名称初稿（可为 None）
            description_draft: 合同描述初稿（可为 None）

        Returns:
            {
                "violations": [...],
                "suggested_name": str,
                "suggested_description": str,
                "compliance_score": int,
            }

        Raises:
            asyncio.TimeoutError: AI 调用超时 → R3.15 ai_timeout (504)
            ComplianceAIError: 一般 AI 错误 → R3.16 (502)
            ComplianceAIInvalidResponseError: JSON 解析两次失败 → R4.11
        """
        drafts = {
            "number_draft": number_draft,
            "name_draft": name_draft,
            "description_draft": description_draft,
        }

        # R4.10: 无规则时跳过模型调用
        if not rules:
            return self._fallback_no_rules(drafts, extracted_text)

        # 构建用户消息
        user_content = self._build_compliance_user_message(
            rules=rules,
            extracted_text=extracted_text,
            text_truncated=text_truncated,
            drafts=drafts,
        )

        for attempt in range(2):  # R4.11: 最多重试 1 次
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": self._COMPLIANCE_SYSTEM_PROMPT,
                            },
                            {"role": "user", "content": user_content},
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=4096,
                        temperature=0.2,
                    ),
                    timeout=270,  # R4.12 - 单次请求最长等 4.5 分钟（SDK max_retries=0，不会叠加）
                )
            except asyncio.TimeoutError:
                raise  # 直接抛给上层，触发 R3.15
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"DeepSeek API error: {type(e).__name__}: {e}")
                raise ComplianceAIError(str(e))

            raw = response.choices[0].message.content or ""
            try:
                parsed = json.loads(raw)
                return self._postprocess(parsed, rules, drafts, extracted_text)
            except (json.JSONDecodeError, ValueError, KeyError):
                if attempt == 1:
                    raise ComplianceAIInvalidResponseError("ai_invalid_response")
                continue  # 第一次失败，进入第二次重试

        # 不应到达此处，但为了类型检查
        raise ComplianceAIInvalidResponseError("ai_invalid_response")

    def _fallback_no_rules(self, drafts: dict, extracted_text: str) -> dict:
        """R4.10: 无规则时的兜底返回"""
        name_draft = drafts.get("name_draft") or ""
        description_draft = drafts.get("description_draft") or ""

        if name_draft.strip():
            suggested_name = name_draft[:200]
        else:
            suggested_name = (
                extracted_text.replace("\n", " ").strip()[:200] or "未命名合同"
            )

        suggested_description = description_draft[:2000] if description_draft else ""

        return {
            "violations": [],
            "suggested_name": suggested_name,
            "suggested_description": suggested_description,
            "compliance_score": 100,
        }

    def _build_compliance_user_message(
        self,
        *,
        rules: list,
        extracted_text: str,
        text_truncated: bool,
        drafts: dict,
    ) -> str:
        """构建发给 LLM 的用户消息"""
        # 规则列表
        rules_lines = []
        for r in rules:
            if hasattr(r, "id"):
                # ORM 对象
                rule_id = str(r.id)
                rule_type = r.rule_type.value if hasattr(r.rule_type, "value") else str(r.rule_type)
                severity = r.severity.value if hasattr(r.severity, "value") else str(r.severity)
                title = r.title
                requirement = r.requirement
            else:
                # dict
                rule_id = str(r.get("id", ""))
                rule_type = r.get("rule_type", "")
                severity = r.get("severity", "")
                title = r.get("title", "")
                requirement = r.get("requirement", "")

            rules_lines.append(
                f"  - id={rule_id}, rule_type={rule_type}, severity={severity}, "
                f"title={title}, requirement={requirement}"
            )

        rules_text = "\n".join(rules_lines)

        number_draft = drafts.get("number_draft")
        name_draft = drafts.get("name_draft")
        description_draft = drafts.get("description_draft")

        return f"""【规则集合】
{rules_text}

【合同文件正文】
{extracted_text or 'null'}

【文件是否被截断】
{str(text_truncated).lower()}

【字段初稿】
number_draft: {number_draft if number_draft else 'null'}
name_draft: {name_draft if name_draft else 'null'}
description_draft: {description_draft if description_draft else 'null'}"""

    def _postprocess(
        self,
        parsed: dict,
        rules: list,
        drafts: dict,
        extracted_text: str,
    ) -> dict:
        """
        R4.3 / R4.4 / R4.6 / R4.7 / R4.8:
        - rule_id 过滤
        - location 与 rule_type 一致性校验
        - 字段初稿为空时丢弃对应 location 的违规
        - severity 强制对齐规则真值
        - 字段长度截断
        - suggested_name 兜底
        """
        # 构建 rule_map（支持 ORM 对象和 dict）
        rule_map = {}
        for r in rules:
            if hasattr(r, "id"):
                rid = str(r.id)
                rule_map[rid] = {
                    "rule_type": r.rule_type.value if hasattr(r.rule_type, "value") else str(r.rule_type),
                    "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
                    "title": r.title,
                }
            else:
                rid = str(r.get("id", ""))
                rule_map[rid] = {
                    "rule_type": r.get("rule_type", ""),
                    "severity": r.get("severity", ""),
                    "title": r.get("title", ""),
                }

        violations = []
        for v in parsed.get("violations", []):
            rid = v.get("rule_id")
            rule = rule_map.get(str(rid) if rid else "")
            if rule is None:
                continue  # R4.3: rule_id 不在集合中 → 丢弃

            if v.get("location") != rule["rule_type"]:
                continue  # R4.3: location 与 rule_type 不一致 → 丢弃

            # R4.6/R4.7/R4.8: 字段初稿为空时丢弃对应 location 的违规
            location = v.get("location", "")
            if location in ("number", "name", "description"):
                draft_val = drafts.get(f"{location}_draft")
                if not draft_val or not str(draft_val).strip():
                    continue

            violations.append(
                {
                    "rule_id": str(rid),
                    "location": location,
                    "excerpt": (v.get("excerpt") or "")[:500],
                    "description": (v.get("description") or "")[:500],
                    "suggestion": (v.get("suggestion") or "")[:500],
                    "severity": rule["severity"],  # 强制对齐规则 severity（R4.5）
                }
            )

        # R4.4: suggested_name 长度归一化与兜底
        suggested_name = (parsed.get("suggested_name") or "")[:200]
        if not suggested_name.strip():
            name_draft = drafts.get("name_draft") or ""
            if name_draft.strip():
                suggested_name = name_draft[:200]
            else:
                suggested_name = (
                    extracted_text.replace("\n", " ").strip()[:200] or "未命名合同"
                )

        suggested_description = (parsed.get("suggested_description") or "")[:2000]

        return {
            "violations": violations,
            "suggested_name": suggested_name,
            "suggested_description": suggested_description,
            "compliance_score": _compute_compliance_score(violations),  # R4.13
        }

    async def generate_summary_with_ai(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> Optional[str]:
        """
        使用AI模型生成智能总结(可选功能)
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            AI生成的总结文本
        """
        try:
            # 获取合同和评审信息
            contract_query = select(Contract).where(Contract.id == contract_id)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
            
            if not contract:
                return None
            
            reviews_query = select(Review).where(Review.contract_id == contract_id)
            reviews_result = await db.execute(reviews_query)
            reviews = reviews_result.scalars().all()
            
            # 构建提示词
            reviews_text = "\n".join([
                f"{r.role} ({r.step}): {r.opinion or '待评审'}"
                for r in reviews if r.opinion
            ])
            
            prompt = f"""
请分析以下合同评审意见,生成一份简洁的总结:

合同名称: {contract.name}
评审意见:
{reviews_text}

请提取:
1. 关键问题和风险点
2. 主要建议
3. 需要关注的事项

总结应简洁明了,不超过200字。
"""
            
            # 调用AI模型
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的合同分析助手"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            return summary
            
        except Exception as e:
            print(f"AI生成总结失败: {str(e)}")
            return None


def _compute_compliance_score(violations: list) -> int:
    """
    R4.13: 100 起扣，must -10/条，should -2/条，clamp 到 [0, 100]。

    Args:
        violations: violation dict 列表，每项含 severity 字段

    Returns:
        0..100 的整数合规评分
    """
    score = 100
    for v in violations:
        severity = v.get("severity", "")
        if severity == "must":
            score -= 10
        elif severity == "should":
            score -= 2
    return max(0, min(100, score))
