export default function ChatInput({
  input,
  loading,
  onInputChange,
  onSubmit,
}) {
  return (
    <div className="chat-input-area">
      <form
        id="chat-form"
        name="chat-form"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
        autoComplete="off"
        style={{ display: "contents" }}
      >
        <div className="chat-input-wrap">
          <input
            id="chat-input"
            name="chat-input"
            className="chat-input"
            type="text"
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            placeholder="Ask about your data..."
            disabled={loading}
            autoComplete="off"
            aria-label="Chat input"
          />
          <button
            id="chat-send"
            name="chat-send"
            className="chat-send-btn"
            type="submit"
            disabled={loading || !input.trim()}
          >
            →
          </button>
        </div>
      </form>
    </div>
  );
}
