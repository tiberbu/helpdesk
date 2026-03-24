/**
 * Compute a line-by-line diff between two HTML strings.
 *
 * HTML tags are stripped before comparison so the diff operates on
 * visible text content. Returns an array of diff lines suitable for
 * rendering in the side-by-side diff view.
 */

export interface DiffLine {
  type: "unchanged" | "added" | "removed";
  content: string;
}

/** Strip HTML tags and decode basic HTML entities to plain text. */
function htmlToText(html: string): string {
  // Use DOMParser when available (browser); fall back to regex in tests.
  if (typeof DOMParser !== "undefined") {
    try {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html || "", "text/html");
      return doc.body.textContent || "";
    } catch {
      // fall through
    }
  }
  return (html || "")
    .replace(/<[^>]*>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"');
}

/** Split text into non-empty lines. */
function splitLines(text: string): string[] {
  return text.split(/\r?\n/);
}

/**
 * Myers-inspired LCS diff: compute the minimum edit sequence between
 * two line arrays using a simple dynamic-programming LCS table.
 */
function lcsMatrix(a: string[], b: string[]): number[][] {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    new Array(n + 1).fill(0)
  );
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  return dp;
}

function backtrack(
  dp: number[][],
  a: string[],
  b: string[],
  i: number,
  j: number,
  result: DiffLine[]
): void {
  if (i === 0 && j === 0) return;
  if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
    backtrack(dp, a, b, i - 1, j - 1, result);
    result.push({ type: "unchanged", content: a[i - 1] });
  } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
    backtrack(dp, a, b, i, j - 1, result);
    result.push({ type: "added", content: b[j - 1] });
  } else {
    backtrack(dp, a, b, i - 1, j, result);
    result.push({ type: "removed", content: a[i - 1] });
  }
}

/**
 * Compute a diff between two HTML content strings.
 *
 * @param htmlA - The older version content (left side).
 * @param htmlB - The newer version content (right side).
 * @returns Array of DiffLine objects describing the changes.
 */
export function computeDiff(htmlA: string, htmlB: string): DiffLine[] {
  const textA = htmlToText(htmlA);
  const textB = htmlToText(htmlB);

  const linesA = splitLines(textA);
  const linesB = splitLines(textB);

  // Guard against extremely large content to avoid stack overflow in recursion.
  if (linesA.length + linesB.length > 5000) {
    // Fall back to a simple two-column view without diff
    return linesA.map((line) => ({ type: "unchanged" as const, content: line }));
  }

  const dp = lcsMatrix(linesA, linesB);
  const result: DiffLine[] = [];
  backtrack(dp, linesA, linesB, linesA.length, linesB.length, result);
  return result;
}
