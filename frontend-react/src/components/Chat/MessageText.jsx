export default function MessageText({ text }) {
  return text.split("**").map((part, index) =>
    index % 2 === 1 ? <strong key={index}>{part}</strong> : <span key={index}>{part}</span>
  );
}
