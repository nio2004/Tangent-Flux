import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { renderMarkdown } from "../src/lib/markdown.ts";

describe("renderMarkdown", () => {
  it("renders headings, emphasis, inline code, lists, and blockquotes", () => {
    const html = renderMarkdown(
      [
        "# Research brief",
        "- **Trace** the source",
        "- Keep `tests` visible",
        "> Approval pending",
      ].join("\n"),
    );

    assert.match(html, /<h3>Research brief<\/h3>/);
    assert.match(html, /<strong>Trace<\/strong>/);
    assert.match(html, /<code>tests<\/code>/);
    assert.match(html, /<blockquote>Approval pending<\/blockquote>/);
  });

  it("escapes unsafe html before rendering markdown syntax", () => {
    const html = renderMarkdown("<script>alert('x')</script> **safe**");

    assert.doesNotMatch(html, /<script>/);
    assert.match(html, /&lt;script&gt;/);
    assert.match(html, /<strong>safe<\/strong>/);
  });
});
