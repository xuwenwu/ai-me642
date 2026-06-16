type AssistantSection = {
  title: string;
  body: string;
  items: string[];
};

const sectionTitles: Record<string, string> = {
  guidance: 'Summary',
  'suggested checks': 'Suggested Checks',
  'caution flags': 'Caution Flags',
  'student next steps': 'Next Steps',
};

function sectionKey(label: string) {
  return label.trim().toLowerCase();
}

function normalizeLine(line: string) {
  return line.replace(/^\s*[-*]\s+/, '').trim();
}

function parseAssistantOutput(text: string): { summary: string; sections: AssistantSection[] } {
  const sections: AssistantSection[] = [];
  let current: AssistantSection | null = null;
  const fallback: string[] = [];

  for (const rawLine of text.replace(/\r\n/g, '\n').split('\n')) {
    const line = rawLine.trim();
    if (!line) continue;

    const headingMatch = line.match(/^([A-Za-z][A-Za-z ]+):\s*(.*)$/);
    if (headingMatch) {
      const key = sectionKey(headingMatch[1]);
      const title = sectionTitles[key];
      if (title) {
        current = { title, body: '', items: [] };
        sections.push(current);
        if (headingMatch[2]) {
          current.body = headingMatch[2].trim();
        }
        continue;
      }
    }

    if (current) {
      if (/^\s*[-*]\s+/.test(rawLine)) {
        current.items.push(normalizeLine(rawLine));
      } else if (current.items.length) {
        current.items.push(line);
      } else {
        current.body = current.body ? `${current.body} ${line}` : line;
      }
    } else {
      fallback.push(line);
    }
  }

  const guidance = sections.find((section) => section.title === 'Summary');
  const summary = guidance?.body || fallback.join(' ');
  return {
    summary,
    sections: sections.filter((section) => section.title !== 'Summary' && (section.body || section.items.length)),
  };
}

export function AssistantOutput({ text }: { text: string }) {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const parsed = parseAssistantOutput(trimmed);
  const showRaw = trimmed.length > 500 || parsed.sections.length > 0;

  return (
    <div className="assistant-output">
      {parsed.summary ? (
        <div className="assistant-output-summary">
          <span>Summary</span>
          <p>{parsed.summary}</p>
        </div>
      ) : null}

      {parsed.sections.length ? (
        <div className="assistant-output-grid">
          {parsed.sections.map((section) => (
            <section className="assistant-output-section" key={section.title}>
              <h4>{section.title}</h4>
              {section.body ? <p>{section.body}</p> : null}
              {section.items.length ? (
                <ul>
                  {section.items.map((item, index) => <li key={`${section.title}-${index}-${item}`}>{item}</li>)}
                </ul>
              ) : null}
            </section>
          ))}
        </div>
      ) : null}

      {showRaw ? (
        <details className="details-panel assistant-output-raw">
          <summary>Full response</summary>
          <pre>{trimmed}</pre>
        </details>
      ) : null}
    </div>
  );
}
