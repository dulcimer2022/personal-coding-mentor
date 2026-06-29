# Personal AI Coding Mentor

Your Notion algorithm notes + GPT-4o-mini, searchable by question.

## Setup

```bash
cd personal_coding_mentor
source venv/bin/activate
```

Fill in `.env` before first run (already done if you're reading this):
- `OPENAI_API_KEY`
- `NOTION_TOKEN`
- `NOTION_CONCEPT_DB_ID`

---

## Daily use

### Start interactive mode
```bash
python mentor.py
```
The model loads once at startup. Ask as many questions as you want — no reload between them. Type `quit` to exit.

---

### QA mode — concept questions
Ask anything about algorithms or data structures.

**Trigger:** any question that isn't code, summarize, or practice.

```
you: what is the difference between BFS and DFS?

[qa]
BFS (Breadth-First Search) is typically used for finding the shortest path in
unweighted graphs and is efficient for problems with constraints on the number
of edges, as it explores all neighbors at the present depth before moving on.
In contrast, DFS (Depth-First Search) is useful for exploring all possible paths
and is often employed in scenarios like topological sorting, where the order of
tasks matters. While BFS is level-oriented and can prune paths based on cost,
DFS uses a stack-like approach and requires additional mechanisms to detect cycles.
```

**Followup questions** — short followups carry the previous answer as context:
```
you: what is BFS?
[qa] BFS explores neighbors level by level...

you: can you give an example of when BFS is better?   ← sees previous answer ✓
[qa] ...

you: why is that faster?                               ← sees turn 2 only, turn 1 is gone
[qa] ...
```

> Followup window is **1 turn back** (the immediately preceding Q&A).
> Longer chains work but only the last exchange is in context — earlier turns are dropped.
> To change this, edit `ctx_history = history[-4:]` in `mentor.py` (e.g. `-8` = 2 turns back).

---

### Summary mode — review your weak spots
Extracts patterns and mistakes from your actual Notion notes.

**Trigger words:** `summarize`, `mistakes`, `pitfalls`, `patterns`, `review`, `weak spots`

```
you: summarize my mistakes in linked list

[summary]
Common pitfalls:
1. "reverse linked list（206）" - Struggled with reversing linked lists, indicating a
   recurring difficulty in manipulating node pointers.
2. "remove node（19, 83）" - Encountered issues with deleting nodes, suggesting
   challenges in understanding how to properly adjust pointers during deletion.

Patterns:
- Difficulty with pointer manipulation, especially in operations that modify
  the structure of the linked list, such as reversing and deleting nodes.
- A tendency to overlook the use of dummy nodes and multiple pointers in more
  complex linked list operations.

Practice problems:
- 206 (Reverse Linked List)
- 19 (Remove Nth Node From End of List)
- 21 (Merge Two Sorted Lists)

Improvements:
- Focus on practicing problems that involve pointer manipulation and structural
  changes in linked lists, specifically using dummy nodes and multiple pointers.
```

---

### Practice mode — get problem suggestions
Returns LeetCode problem IDs matched to your notes for a topic.

**Trigger words:** `practice`, `suggest`, `problems`, `questions`, `drill`

```
you: suggest practice problems for sliding window

[practice]
Suggested problems: 3, 76, 239, 567, 424, 209, 438, 1004, 159, 395
```

---

### Debug mode — get a hint on your code
Type `debug` to enter code paste mode. The mentor gives a targeted hint — **never a full solution**.

```
you: debug
Paste your code. Type END on a new line when done:
> def twoSum(nums, target):
>     for i in range(len(nums)):
>         for j in range(len(nums)):
>             if nums[i] + nums[j] == target:
>                 return [i, j]
> END
What's the issue? (press Enter to skip): why does it return wrong indices?

[debug]
Issue: The code may return the same index for both i and j when i equals j,
which is not valid for the two-sum problem.
Root cause: The nested loops do not prevent the same element from being used
twice, leading to incorrect results.
Hint: How can you modify the inner loop to ensure that i and j are not the same?
Related: [1]
```

**Followup after debug** — same 1-turn window applies:
```
you: can you explain what inner loop means here?   ← sees the debug answer above ✓
```

---

### Sync Notion notes
Run this after you update your Notion pages:
```
you: sync
```
Or from terminal:
```bash
python mentor.py sync
```

---

## One-shot mode (no interactive session)
```bash
python mentor.py "what is the sliding window pattern?"
python mentor.py "summarize my mistakes in dynamic programming"
python mentor.py sync
```

---

## Files

| File | What it does |
|---|---|
| `notion_loader.py` | Fetches pages from Notion API |
| `chunker.py` | Splits pages into 500-char chunks |
| `vector_store.py` | Stores/searches chunks in ChromaDB |
| `classifier.py` | Detects query mode (debug/summary/practice/qa) |
| `retriever.py` | Finds relevant chunks for a query |
| `prompt_builder.py` | Builds mode-specific prompts |
| `llm.py` | Calls GPT-4o-mini |
| `sync.py` | Incremental Notion → ChromaDB sync |
| `mentor.py` | CLI entry point |
| `data/chroma/` | Local vector database (gitignored) |
