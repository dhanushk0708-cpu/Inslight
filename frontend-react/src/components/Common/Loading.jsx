export default function Loading({ text = "Analyzing..." }) {
  return (
    <div className="loading-container fade-in">
      <div className="loading-spinner" />
      <div className="loading-text">{text}</div>
    </div>
  );
}
