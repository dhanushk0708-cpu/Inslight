import MessageText from "./MessageText";

export default function ChatMessages({
  loading,
  messageEndRef,
  messages,
  onSuggestionClick,
}) {
  return (
    <div className="chat-messages">
      {messages.map((message, index) => (
        <div key={`${message.role}-${message.time}-${index}`} className={`msg ${message.role}`}>
          <div className="msg-avatar">{message.role === "user" ? "👤" : "✨"}</div>
          <div>
            <div className="msg-bubble">
              <MessageText text={message.text} />
            </div>
            {message.suggestions?.length > 0 && (
              <div className="chat-suggestions">
                {message.suggestions.map((suggestion, suggestionIndex) => (
                  <button
                    key={`${suggestion}-${suggestionIndex}`}
                    id={`sug-${index}-${suggestionIndex}`}
                    name={`sug-${index}-${suggestionIndex}`}
                    className="chat-suggestion-chip"
                    type="button"
                    onClick={() => onSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            <div className="msg-time">{message.time}</div>
          </div>
        </div>
      ))}

      {loading && (
        <div className="msg ai">
          <div className="msg-avatar">✨</div>
          <div className="msg-bubble">
            <div className="typing">
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      )}

      <div ref={messageEndRef} />
    </div>
  );
}
