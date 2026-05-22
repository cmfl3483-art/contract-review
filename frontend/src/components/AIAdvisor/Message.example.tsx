import Message from './Message';
import type { Message as MessageType } from '../../types';

// Example messages for demonstration
const exampleMessages: MessageType[] = [
  {
    id: '1',
    role: 'user',
    content: '法务意见是什么？',
    timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // 10分钟前
  },
  {
    id: '2',
    role: 'assistant',
    content:
      '根据评审记录，法务部门提出了以下意见：\n\n1. 合同条款需要明确违约责任\n2. 建议增加保密条款\n3. 付款方式需要进一步协商',
    timestamp: new Date(Date.now() - 9 * 60 * 1000).toISOString(), // 9分钟前
  },
  {
    id: '3',
    role: 'user',
    content: '有哪些风险项？',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5分钟前
  },
  {
    id: '4',
    role: 'assistant',
    content:
      '当前合同存在以下风险项：\n\n• 财务部门标记的付款条件不明确\n• 法务部门指出的违约责任条款缺失\n• 业务部门提出的交付时间过于紧张\n\n建议优先处理这些问题。',
    timestamp: new Date(Date.now() - 4 * 60 * 1000).toISOString(), // 4分钟前
  },
  {
    id: '5',
    role: 'user',
    content: '我有哪些待处理任务？',
    timestamp: new Date(Date.now() - 1 * 60 * 1000).toISOString(), // 1分钟前
  },
  {
    id: '6',
    role: 'assistant',
    content: '您当前有 2 个待处理的评审任务：\n\n1. 采购合同 - 法务初审\n2. 销售合同 - 财务审核\n\n请及时完成审批。',
    timestamp: new Date().toISOString(), // 刚刚
  },
];

/**
 * Message Component Examples
 *
 * This file demonstrates various use cases of the Message component.
 */
const MessageExamples = () => {
  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Message Component Examples</h2>

      <div style={{ marginTop: '20px' }}>
        <h3>User Message</h3>
        <Message message={exampleMessages[0]} currentUserName="张三" />
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Assistant Message</h3>
        <Message message={exampleMessages[1]} />
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Conversation Flow</h3>
        <div style={{ background: '#fff', padding: '16px', borderRadius: '8px' }}>
          {exampleMessages.map((message) => (
            <Message key={message.id} message={message} currentUserName="张三" />
          ))}
        </div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Long Content Message</h3>
        <Message
          message={{
            id: '7',
            role: 'assistant',
            content:
              '这是一段很长的回复内容，用于演示消息组件如何处理长文本。在实际使用中，AI 可能会返回包含详细分析、多个要点或长篇解释的内容。组件应该能够正确地显示这些内容，并保持良好的可读性和布局。\n\n消息气泡会自动调整大小以适应内容，同时保持最大宽度限制，确保在不同屏幕尺寸下都能良好显示。',
            timestamp: new Date().toISOString(),
          }}
        />
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Short Message</h3>
        <Message
          message={{
            id: '8',
            role: 'user',
            content: '好的',
            timestamp: new Date().toISOString(),
          }}
          currentUserName="张三"
        />
      </div>
    </div>
  );
};

export default MessageExamples;
