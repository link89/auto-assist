RETRIVE_FACULTY_MEBERS = """
Your job is to retrive information of faculty members from a markdown file.
The markdown file will contain multiple faculty members.

A faculty member object can be defined as the following TypeScript interface:

```typescript
interface FaucultyMember {
    name: string;
    title?: string;  // the title of the faculty member, e.g. Professor, Associate Professor, Prof, Enginner, etc.
    email?: string;
    institue?: string;  // the name of institue the faculty member belongs to
    department?: string;  // the department the faculty member belongs to
    introduction?: string;  // the introduction of the faculty member
    profile_url?: string; // the url to the detailed profile of the faculty member
    avarar_url?: string;  // the url to the avatar image of the faculty member
    urls?: string[];  // other urls related to the faculty member
}
```

You must serialize every racultyMember object you find in the markdown file to a single line of json object, aka jsonl format,
and put them in a json block, for example:
```json
{"name": "Alice", "title": "Associate Professor", "profile_url": "https://example.org/alice", "email": "alice@example.org", "department": "Computer Science"}
{"name": "Bob", "title": "Professor", "profile_url": "https://example.org/bob"}
```
Note that the data in example above is not real, you should replace them with the real data you find.
You should try to find as much information as possible for each faculty member, but if you can't find some information, just leave them empty.
""".strip()