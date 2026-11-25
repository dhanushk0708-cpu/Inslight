import React from "react";

interface MarkdownRendererProps {
  content: string;
}

function renderInline(text: string): React.ReactNode[] {
  // Tokenize **bold**, *italic*, and `code`
  const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return (
        <strong key={idx} style={{ color: "#f9fafb", fontWeight: 700 }}>
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return (
        <em key={idx} style={{ color: "#d1d5db", fontStyle: "italic" }}>
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code
          key={idx}
          style={{
            background: "rgba(255, 255, 255, 0.08)",
            padding: "1px 5px",
            borderRadius: 4,
            fontSize: "0.9em",
            color: "#93c5fd",
            fontFamily: "monospace",
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  const lines = content.split(/\r?\n/);
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      i++;
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(trimmed)) {
      elements.push(
        <hr
          key={`hr-${i}`}
          style={{
            border: "none",
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
            margin: "10px 0",
          }}
        />
      );
      i++;
      continue;
    }

    // Headings (#, ##, ###, ####)
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const fontSize = level === 1 ? 17 : level === 2 ? 15.5 : level === 3 ? 14 : 13;
      elements.push(
        <div
          key={`h-${i}`}
          style={{
            fontSize,
            fontWeight: 700,
            color: "#f3f4f6",
            marginTop: elements.length > 0 ? 10 : 2,
            marginBottom: 4,
          }}
        >
          {renderInline(headingMatch[2])}
        </div>
      );
      i++;
      continue;
    }

    // Unordered list (- or *)
    if (/^[-*]\s+/.test(trimmed)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        const lineText = lines[i].trim().replace(/^[-*]\s+/, "");
        const isNested = /^\s{2,}/.test(lines[i]);
        items.push(
          <li
            key={`ul-li-${i}`}
            style={{
              marginBottom: 3,
              marginLeft: isNested ? 14 : 0,
              lineHeight: 1.5,
            }}
          >
            {renderInline(lineText)}
          </li>
        );
        i++;
      }
      elements.push(
        <ul
          key={`ul-${i}`}
          style={{
            margin: "4px 0 8px 0",
            paddingLeft: 18,
            listStyleType: "disc",
          }}
        >
          {items}
        </ul>
      );
      continue;
    }

    // Ordered list (1. 2. 3.) with optional nested bullet sub-items
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: React.ReactNode[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        const mainText = lines[i].trim().replace(/^\d+\.\s+/, "");
        i++;
        const subItems: React.ReactNode[] = [];
        while (i < lines.length && /^\s+[-*]\s+/.test(lines[i])) {
          const subText = lines[i].trim().replace(/^[-*]\s+/, "");
          subItems.push(
            <li key={`ol-sub-${i}`} style={{ marginBottom: 2, lineHeight: 1.45 }}>
              {renderInline(subText)}
            </li>
          );
          i++;
        }
        // Also skip single blank lines between numbered items inside the same list
        while (i < lines.length && !lines[i].trim() && i + 1 < lines.length && /^\d+\.\s+/.test(lines[i + 1].trim())) {
          i++;
        }
        items.push(
          <li key={`ol-li-${i}`} style={{ marginBottom: 6, lineHeight: 1.5 }}>
            <div>{renderInline(mainText)}</div>
            {subItems.length > 0 && (
              <ul style={{ margin: "4px 0 2px 0", paddingLeft: 16, listStyleType: "circle" }}>
                {subItems}
              </ul>
            )}
          </li>
        );
      }
      elements.push(
        <ol
          key={`ol-${i}`}
          style={{
            margin: "4px 0 8px 0",
            paddingLeft: 18,
          }}
        >
          {items}
        </ol>
      );
      continue;
    }

    // Regular paragraph
    elements.push(
      <p key={`p-${i}`} style={{ margin: "0 0 6px 0", lineHeight: 1.55 }}>
        {renderInline(trimmed)}
      </p>
    );
    i++;
  }

  return <div className="markdown-body">{elements}</div>;
};
