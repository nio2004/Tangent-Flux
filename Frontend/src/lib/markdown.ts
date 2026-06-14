function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderInline(value: string) {
  return value
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

export function renderMarkdown(markdown: string) {
  const lines = markdown.split(/\r?\n/);
  const output: string[] = [];
  let listOpen = false;

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (!trimmed) {
      if (listOpen) {
        output.push("</ul>");
        listOpen = false;
      }
      return;
    }

    if (trimmed.startsWith("- ")) {
      if (!listOpen) {
        output.push("<ul>");
        listOpen = true;
      }
      output.push(`<li>${renderInline(escapeHtml(trimmed.slice(2)))}</li>`);
      return;
    }

    if (listOpen) {
      output.push("</ul>");
      listOpen = false;
    }

    if (trimmed.startsWith("# ")) {
      output.push(`<h3>${renderInline(escapeHtml(trimmed.slice(2)))}</h3>`);
      return;
    }

    if (trimmed.startsWith("## ")) {
      output.push(`<h4>${renderInline(escapeHtml(trimmed.slice(3)))}</h4>`);
      return;
    }

    if (trimmed.startsWith("> ")) {
      output.push(`<blockquote>${renderInline(escapeHtml(trimmed.slice(2)))}</blockquote>`);
      return;
    }

    output.push(`<p>${renderInline(escapeHtml(trimmed))}</p>`);
  });

  if (listOpen) {
    output.push("</ul>");
  }

  return output.join("");
}
