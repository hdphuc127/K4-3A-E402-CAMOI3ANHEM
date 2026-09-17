import { Fragment, type ReactNode } from "react";

// Deliberately limited Markdown subset. React escapes text; raw HTML is never executed.
function inline(text: string, depth = 0): ReactNode {
  if (depth > 12) return text;
  const tokens =
    /\\([\\`*_])|(`+)([^`\n]+?)\2|\*\*\*([^\n]+?)\*\*\*|___([^\n]+?)___|\*\*([^\n]+?)\*\*|__([^\n]+?)__|\*([^*\n]+?)\*|(?<![\p{L}\p{N}])_([^_\n]+?)_(?![\p{L}\p{N}])/gu;
  const nodes: ReactNode[] = [];
  let offset = 0;
  for (const match of text.matchAll(tokens)) {
    const position = match.index;
    nodes.push(text.slice(offset, position));
    let node: ReactNode;
    if (match[1] !== undefined) node = match[1];
    else if (match[3] !== undefined) {
      node = (
        <code className="rounded bg-primary/5 px-1 py-0.5 font-mono text-[0.9em]">{match[3]}</code>
      );
    } else if (match[4] !== undefined || match[5] !== undefined) {
      node = (
        <strong>
          <em>{inline(match[4] ?? match[5]!, depth + 1)}</em>
        </strong>
      );
    } else if (match[6] !== undefined || match[7] !== undefined) {
      node = <strong>{inline(match[6] ?? match[7]!, depth + 1)}</strong>;
    } else {
      node = <em>{inline(match[8] ?? match[9]!, depth + 1)}</em>;
    }
    nodes.push(<Fragment key={position}>{node}</Fragment>);
    offset = position + match[0].length;
  }
  nodes.push(text.slice(offset));
  return nodes;
}

const listItem = /^\s{0,3}(?:([-+*])|(\d+)[.)])\s+(.+)$/;

export function ChatMarkdown({ text }: { text: string }) {
  const lines = text.replace(/\r\n?/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    if (!lines[index]!.trim()) {
      index++;
      continue;
    }
    const first = lines[index]!.match(listItem);
    if (first) {
      const start = index;
      const ordered = first[2] !== undefined;
      const items: ReactNode[] = [];
      while (index < lines.length) {
        const item = lines[index]!.match(listItem);
        if (!item || (item[2] !== undefined) !== ordered) break;
        const itemIndex = index++;
        let content = item[3]!;
        // Indented continuation lines stay with their list item.
        while (
          index < lines.length &&
          /^\s{2,}\S/.test(lines[index]!) &&
          !listItem.test(lines[index]!)
        ) {
          content += `\n${lines[index++]!.trimStart()}`;
        }
        items.push(
          <li key={itemIndex} className="whitespace-pre-line break-words">
            {inline(content)}
          </li>,
        );
      }
      blocks.push(
        ordered ? (
          <ol
            key={start}
            start={Number(first[2])}
            className="list-outside list-decimal space-y-1 pl-5"
          >
            {items}
          </ol>
        ) : (
          <ul key={start} className="list-outside list-disc space-y-1 pl-5">
            {items}
          </ul>
        ),
      );
    } else {
      const start = index;
      const paragraph: string[] = [];
      while (index < lines.length && lines[index]!.trim() && !listItem.test(lines[index]!)) {
        paragraph.push(lines[index++]!);
      }
      blocks.push(
        <p key={start} className="whitespace-pre-line break-words">
          {inline(paragraph.join("\n"))}
        </p>,
      );
    }
  }

  return <div className="space-y-2 whitespace-normal">{blocks}</div>;
}
