FACULTY_OBJECT_SCHEMA = """
```typescript
interface FaucultyMember {
    name: string;
    title?: string;  // the title of the faculty member, e.g. Professor, Associate Professor, Prof, Enginner, etc.
    email?: string;
    introduction?: string;  // the introduction of the faculty member, e.g. research interests, experience, etc.
    profile_url?: string; // the url to the detailed profile of the faculty member
}
```
""".strip()


RETRIVE_FACULTY_MEBERS = """
Your job is to retrive information of faculty members from a markdown file.
The markdown file will contain multiple faculty members.

A faculty member object can be defined as the following TypeScript interface:

FACULTY_OBJECT_SCHEMA

You must serialize every racultyMember object you find in the markdown file to a single line of json object, aka jsonl format,
and put them in a json block, for example:
```json
{"name": "Alice", "title": "Associate Professor", "profile_url": "https://example.org/alice", "email": "alice@example.org", "introduction": "research interests include AI, machine learning, etc."}
{"name": "Bob", "title": "Professor", "profile_url": "https://example.org/bob"}
```
Note that the data in example above is not real, you should replace them with the real data you find.
You should try to find as much information as possible for each faculty member, but if you can't find some information, just leave them empty.
""".strip().replace('FACULTY_OBJECT_SCHEMA', FACULTY_OBJECT_SCHEMA)


FIX_FACULTY_JSON = """
Your job is to fix the invalid json string that contains faculty member information.
A valid json string should respect the following typescript interface:

FACULTY_OBJECT_SCHEMA

You need to fix it according to the interface above, and generate a new json string in json code block.

For example:
```json
{"name": "Alice", "title": "Associate Professor", "profile_url": "https://example.org/alice", "email": "alice@example.org"}
```

Note that the data in example above is not real, you should replace them with the real data you find.
You should try to find as much information as possible for each faculty member, but if you can't find some information, just leave them empty.
""".strip().replace('FACULTY_OBJECT_SCHEMA', FACULTY_OBJECT_SCHEMA)