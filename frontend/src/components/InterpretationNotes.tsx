import type { InterpretationNote } from '@/lib/types';

export function InterpretationNotes({ notes }: { notes: InterpretationNote[] }) {
  if (!notes.length) return null;

  return (
    <section className="interpretation-notes">
      <h3>Interpretation Cues</h3>
      <div className="note-list">
        {notes.map((note) => (
          <article key={`${note.topic}-${note.evidence}`} className={`note-card ${note.status}`}>
            <div className="note-heading">
              <strong>{note.topic}</strong>
              <span>{note.status.replace('_', ' ')}</span>
            </div>
            <p>{note.message}</p>
            {note.evidence ? <p className="muted">{note.evidence}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
