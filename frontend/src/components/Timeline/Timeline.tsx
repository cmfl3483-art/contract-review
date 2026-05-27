import React, { useMemo } from 'react';
import { Empty, Spin } from 'antd';
import { useReviews } from '../../hooks';
import AISummaryCard from './AISummaryCard';
import ReviewCard from './ReviewCard';
import TopLevelCommentCard from './TopLevelCommentCard';
import CommentInput from './CommentInput';
import './Timeline.css';

interface TimelineProps {
  contractId: string;
}

const Timeline: React.FC<TimelineProps> = ({ contractId }) => {
  const { data, isLoading, error } = useReviews(contractId);

  const { reviews = [], aiSummary = null, topLevelComments = [] } = data ?? {};

  const validReviews = reviews.filter(
    (review) =>
      review.opinion &&
      review.opinion.trim() !== '' &&
      review.opinion !== '待评审' &&
      review.opinion !== '待处理'
  );

  const sortedItems = useMemo(() => {
    type TimelineItem =
      | { type: 'review'; data: typeof validReviews[0] }
      | { type: 'comment'; data: typeof topLevelComments[0] };
    const items: TimelineItem[] = [];
    for (const r of validReviews) items.push({ type: 'review', data: r });
    for (const c of topLevelComments) items.push({ type: 'comment', data: c });
    items.sort((a, b) => {
      const timeA = new Date(a.data.createdAt).getTime();
      const timeB = new Date(b.data.createdAt).getTime();
      if (isNaN(timeA)) return 1;
      if (isNaN(timeB)) return -1;
      return timeB - timeA;
    });
    return items;
  }, [data]);

  const hasAnyComment = validReviews.length > 0 || topLevelComments.length > 0;

  // 关键：永远渲染 CommentInput，无论数据加载状态如何
  return (
    <div className="timeline-container">
      <div className="timeline">
        {isLoading && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" tip="加载中..." />
          </div>
        )}
        {error && !isLoading && (
          <Empty description={error instanceof Error ? error.message : '加载失败'} />
        )}
        {!isLoading && !error && (
          <>
            {aiSummary && <AISummaryCard summary={aiSummary} />}
            {!hasAnyComment ? (
              <Empty description="暂无评审记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              sortedItems.map((item) =>
                item.type === 'review' ? (
                  <ReviewCard key={item.data.id} review={item.data} contractId={contractId} />
                ) : (
                  <TopLevelCommentCard key={item.data.id} comment={item.data} contractId={contractId} />
                )
              )
            )}
          </>
        )}
      </div>
      <CommentInput contractId={contractId} />
    </div>
  );
};

export default Timeline;
