/**
 * React Query Hooks 使用示例
 *
 * 这个文件展示了如何在组件中使用 React Query hooks
 */

import { useState } from 'react';
import { Button, List, Spin, message } from 'antd';
import {
  useContractList,
  useContractDetail,
  useCreateContract,
  useReviews,
  useApproveReview,
  useAddComment,
  useLikeReview,
  useUploadAttachment,
  useAISummary,
  useAIAdvisor,
  useCurrentUser,
  usePendingCount,
} from './index';

/**
 * 示例 1: 获取合同列表
 */
export function ContractListExample() {
  const [filter, setFilter] = useState<'all' | '进行中' | '已完成' | '待我处理' | '抄送我'>('all');
  const [search, setSearch] = useState('');

  const { data, isLoading, error } = useContractList(filter, search);

  if (isLoading) return <Spin />;
  if (error) return <div>错误: {error.message}</div>;

  return (
    <div>
      <div>
        <Button onClick={() => setFilter('all')}>全部</Button>
        <Button onClick={() => setFilter('进行中')}>进行中</Button>
        <Button onClick={() => setFilter('已完成')}>已完成</Button>
        <Button onClick={() => setFilter('待我处理')}>待我处理</Button>
      </div>
      <input
        type="text"
        placeholder="搜索合同"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <List
        dataSource={data?.contracts}
        renderItem={(contract) => (
          <List.Item key={contract.id}>
            {contract.name} - {contract.status}
          </List.Item>
        )}
      />
      <div>总数: {data?.total}</div>
      <div>待办: {data?.pendingCount}</div>
    </div>
  );
}

/**
 * 示例 2: 获取合同详情
 */
export function ContractDetailExample({ contractId }: { contractId: string }) {
  const { data, isLoading, error } = useContractDetail(contractId);

  if (isLoading) return <Spin />;
  if (error) return <div>错误: {error.message}</div>;

  return (
    <div>
      <h2>{data?.contract.name}</h2>
      <p>{data?.contract.description}</p>
      <h3>评审人</h3>
      <List
        dataSource={data?.reviewers}
        renderItem={(reviewer) => (
          <List.Item key={reviewer.id}>
            {reviewer.name} - {reviewer.status}
          </List.Item>
        )}
      />
      <h3>附件</h3>
      <List
        dataSource={data?.attachments}
        renderItem={(group) => (
          <List.Item key={group.fileName}>
            {group.fileName} ({group.versionCount} 个版本)
          </List.Item>
        )}
      />
    </div>
  );
}

/**
 * 示例 3: 创建合同
 */
export function CreateContractExample() {
  const { mutate, isPending } = useCreateContract();

  const handleCreate = () => {
    mutate(
      {
        name: '新合同',
        description: '合同描述',
        reviewers: ['user1', 'user2'],
        ccUsers: ['user3'],
      },
      {
        onSuccess: (data) => {
          message.success(`合同创建成功: ${data.contractId}`);
        },
        onError: (error) => {
          message.error(`创建失败: ${error.message}`);
        },
      }
    );
  };

  return (
    <Button onClick={handleCreate} loading={isPending}>
      创建合同
    </Button>
  );
}

/**
 * 示例 4: 获取评审记录
 */
export function ReviewsExample({ contractId }: { contractId: string }) {
  const { data, isLoading } = useReviews(contractId);

  if (isLoading) return <Spin />;

  return (
    <div>
      {data?.aiSummary && (
        <div>
          <h3>AI 智能总结</h3>
          <p>状态: {data.aiSummary.approvalStatus}</p>
          <p>
            进度: {data.aiSummary.completedCount}/{data.aiSummary.totalCount}
          </p>
          <h4>关键问题:</h4>
          <ul>
            {data.aiSummary.keyIssues.map((issue, index) => (
              <li key={index}>
                {issue.issue}
                {issue.solution && <p>解决方案: {issue.solution}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
      <h3>评审记录</h3>
      <List
        dataSource={data?.reviews}
        renderItem={(review) => (
          <List.Item key={review.id}>
            {review.reviewer?.name}: {review.opinion || '待评审'}
            <span>👍 {review.likes}</span>
          </List.Item>
        )}
      />
    </div>
  );
}

/**
 * 示例 5: 同意评审
 */
export function ApproveReviewExample({
  contractId,
  reviewId,
}: {
  contractId: string;
  reviewId: string;
}) {
  const { mutate, isPending } = useApproveReview();

  const handleApprove = () => {
    mutate(
      {
        contractId,
        reviewId,
        opinion: '同意并通过',
      },
      {
        onSuccess: () => {
          message.success('审批成功');
        },
        onError: (error) => {
          message.error(`审批失败: ${error.message}`);
        },
      }
    );
  };

  return (
    <Button onClick={handleApprove} loading={isPending}>
      同意
    </Button>
  );
}

/**
 * 示例 6: 添加评论
 */
export function AddCommentExample({ contractId }: { contractId: string }) {
  const [content, setContent] = useState('');
  const { mutate, isPending } = useAddComment();

  const handleSubmit = () => {
    if (!content.trim()) return;

    mutate(
      {
        contractId,
        content,
      },
      {
        onSuccess: () => {
          message.success('评论成功');
          setContent('');
        },
        onError: (error) => {
          message.error(`评论失败: ${error.message}`);
        },
      }
    );
  };

  return (
    <div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="输入评论"
      />
      <Button onClick={handleSubmit} loading={isPending}>
        发送
      </Button>
    </div>
  );
}

/**
 * 示例 7: 点赞
 */
export function LikeExample({ reviewId, contractId }: { reviewId: string; contractId: string }) {
  const { mutate, isPending } = useLikeReview();

  const handleLike = () => {
    mutate({ reviewId, contractId });
  };

  return (
    <Button onClick={handleLike} loading={isPending}>
      👍 点赞
    </Button>
  );
}

/**
 * 示例 8: 上传附件
 */
export function UploadAttachmentExample({ contractId }: { contractId: string }) {
  const { mutate, isPending } = useUploadAttachment();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    mutate(
      {
        contractId,
        file,
      },
      {
        onSuccess: () => {
          message.success('上传成功');
        },
        onError: (error) => {
          message.error(`上传失败: ${error.message}`);
        },
      }
    );
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} disabled={isPending} />
      {isPending && <Spin />}
    </div>
  );
}

/**
 * 示例 9: AI 智能总结
 */
export function AISummaryExample({ contractId }: { contractId: string }) {
  const { data, isLoading, error } = useAISummary(contractId);

  if (isLoading) return <Spin />;
  if (error) return <div>AI 服务暂时不可用</div>;
  if (!data) return null;

  return (
    <div>
      <h3>AI 智能总结</h3>
      <p>审批状态: {data.approvalStatus === 'completed' ? '已全部通过' : '审批进行中'}</p>
      <p>
        进度: {data.completedCount}/{data.totalCount}
      </p>
      <p>评审意见总数: {data.reviewCount}</p>
      <h4>关键问题:</h4>
      <ul>
        {data.keyIssues.map((issue, index) => (
          <li key={index}>
            <strong>{issue.issue}</strong>
            {issue.solution && <p>解决方案: {issue.solution}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * 示例 10: AI 顾问
 */
export function AIAdvisorExample({ contractId }: { contractId: string }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const { mutate, isPending } = useAIAdvisor();

  const handleAsk = () => {
    if (!question.trim()) return;

    mutate(
      {
        contractId,
        question,
      },
      {
        onSuccess: (data) => {
          setAnswer(data);
          setQuestion('');
        },
        onError: (error) => {
          message.error(`AI 服务失败: ${error.message}`);
        },
      }
    );
  };

  return (
    <div>
      <h3>AI 合同顾问</h3>
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="输入问题"
      />
      <Button onClick={handleAsk} loading={isPending}>
        提问
      </Button>
      {answer && (
        <div>
          <h4>回答:</h4>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}

/**
 * 示例 11: 当前用户
 */
export function CurrentUserExample() {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) return <Spin />;
  if (!user) return null;

  return (
    <div>
      <p>用户: {user.name}</p>
      <p>角色: {user.role}</p>
      <p>部门: {user.department}</p>
    </div>
  );
}

/**
 * 示例 12: 待办数量
 */
export function PendingCountExample() {
  const { data: count } = usePendingCount();

  return (
    <div>
      待办数量: <span style={{ color: 'red' }}>{count || 0}</span>
    </div>
  );
}
