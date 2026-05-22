# ChatInput Component

## Overview

The `ChatInput` component provides a chat input interface for the AI Advisor feature. It includes a text input field and a send button, with support for keyboard shortcuts and loading states.

## Features

- **Text Input**: Input field for typing messages
- **Send Button**: Button to submit messages
- **Enter Key Support**: Press Enter to send messages (Shift+Enter is ignored)
- **Loading State**: Disables input and button during message processing
- **Input Validation**: Prevents sending empty or whitespace-only messages
- **Auto-clear**: Clears input field after successful send

## Props

```typescript
interface ChatInputProps {
  onSend: (message: string) => void;  // Callback when message is sent
  loading?: boolean;                   // Loading state (disables input)
  placeholder?: string;                // Placeholder text for input
}
```

## Usage

### Basic Usage

```tsx
import ChatInput from './ChatInput';

function MyComponent() {
  const handleSend = (message: string) => {
    console.log('Message sent:', message);
  };

  return <ChatInput onSend={handleSend} />;
}
```

### With Loading State

```tsx
import { useState } from 'react';
import ChatInput from './ChatInput';

function MyComponent() {
  const [loading, setLoading] = useState(false);

  const handleSend = async (message: string) => {
    setLoading(true);
    try {
      await sendMessageToAPI(message);
    } finally {
      setLoading(false);
    }
  };

  return <ChatInput onSend={handleSend} loading={loading} />;
}
```

### Custom Placeholder

```tsx
import ChatInput from './ChatInput';

function MyComponent() {
  const handleSend = (message: string) => {
    console.log('Message sent:', message);
  };

  return (
    <ChatInput 
      onSend={handleSend} 
      placeholder="Type your question here..." 
    />
  );
}
```

## Behavior

### Sending Messages

1. **Click Send Button**: Click the send button to submit the message
2. **Press Enter**: Press Enter key to submit the message
3. **Shift+Enter**: Pressing Shift+Enter does NOT send the message (for potential multi-line support)

### Input Validation

- Empty messages are not sent
- Messages with only whitespace are not sent
- Leading and trailing whitespace is trimmed before sending

### Loading State

When `loading` is `true`:
- Input field is disabled
- Send button is disabled and shows loading spinner
- Messages cannot be sent

### Button State

- Send button is disabled when input is empty
- Send button is enabled when input has content
- Send button is disabled during loading

## Styling

The component uses Ant Design's `Input`, `Button`, and `Space.Compact` components for consistent styling with the rest of the application.

## Requirements Mapping

This component implements the following requirements:

- **需求 7.8**: Support sending questions via Enter key
- **需求 5.1**: Comment input box (similar pattern)
- **需求 5.2**: Submit via Enter key or send button
- **需求 10.5**: Placeholder text for input fields
- **需求 10.6**: Focus state visual feedback

## Testing

Unit tests are available in `ChatInput.test.tsx` covering:

- Rendering of input and button
- Custom placeholder text
- Input value changes
- Sending via button click
- Sending via Enter key
- Shift+Enter behavior (should not send)
- Empty message validation
- Whitespace-only message validation
- Loading state behavior
- Button disabled state
- Message trimming

Run tests with:
```bash
npm test -- ChatInput.test.tsx
```

## Integration

The ChatInput component is used in the AIAdvisor component:

```tsx
import ChatInput from './ChatInput';

function AIAdvisor() {
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async (message: string) => {
    setLoading(true);
    try {
      // Send message to AI service
      const response = await sendToAI(message);
      // Handle response
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-advisor">
      {/* Messages display */}
      <div className="ai-advisor-input">
        <ChatInput onSend={handleSendMessage} loading={loading} />
      </div>
    </div>
  );
}
```

## Accessibility

- Input field has proper placeholder text
- Button has descriptive text and icon
- Keyboard navigation is fully supported
- Loading state is properly communicated through disabled state

## Future Enhancements

Potential improvements for future versions:

1. **Multi-line Support**: Support Shift+Enter for multi-line messages
2. **Character Counter**: Show character count for long messages
3. **Emoji Picker**: Add emoji picker button
4. **Voice Input**: Support voice-to-text input
5. **File Attachments**: Support attaching files to messages
6. **Message History**: Navigate through previous messages with arrow keys
