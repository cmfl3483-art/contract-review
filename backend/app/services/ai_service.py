"""
AI服务层
实现智能总结生成和合同顾问问答功能
支持DeepSeek API和自部署模型
"""
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


class AIService:
    """AI服务类"""
    
    def __init__(self):
        # 初始化OpenAI兼容客户端
        self.client = AsyncOpenAI(
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_API_BASE,
            timeout=settings.AI_TIMEOUT
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
            sections.append(f"- {name}（{r.role}）：{status_text} | 意见：{opinion_text}")
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
                sections.append(f"- {author_name}{reply_to}：{c.content or ''}")
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
            "规则：\n"
            "1. 内容务必简洁，每条不超过两句话。\n"
            "2. 使用评审人和评论者的真实姓名。\n"
            "3. 如果风险已有应对措施，说明措施内容；未解决的标注「未解决」。\n"
            "4. 不要复述原文，要提炼核心意思。\n"
            "5. 总字数控制在 300 字以内。"
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
                max_tokens=600,
                temperature=0.3,
            )
            answer = response.choices[0].message.content
            return answer.strip() if answer else "抱歉，未能生成总结。"
        except Exception as e:
            print(f"AI总结调用失败: {str(e)}")
            # 降级：回退到 DB 直查
            return await self._summarize_progress_and_opinions(
                contract_id=str(contract.id),
                reviews=reviews,
                db=db,
            )

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
                max_tokens=800,
                temperature=0.3,  # 低温度，减少幻觉
            )
            answer = response.choices[0].message.content
            return answer.strip() if answer else "抱歉，未能生成回答。"
        except Exception as e:
            print(f"LLM调用失败: {str(e)}")
            return "抱歉，AI服务暂时不可用，请稍后重试。"

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
