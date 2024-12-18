RETRIVE_FACULTY_MEMBERS = """
Your job is to retrive information of faculty members from a markdown file.
The markdown file will contain multiple faculty members.

A faculty member object can be defined as the following TypeScript interface:
```typescript
interface Fauculty {
    name: string;
    title?: string;  // the title of the faculty member, e.g. Professor, Associate Professor, Prof, Enginner, etc. You can infer this from the name or your own knowledge about this person if it is not explicitly mentioned. The title must be as elaborate as possible, e.g. use "Associate Professor" instead of "Professor".
    profile_url?: string; // the url to the detailed profile of the faculty member
}
```
You must serialize every Faculty object you find in the markdown file to a single line of json object, aka jsonl format,
and put them in a json block, for example:
```json
{"name":"Alice","title":"Associate Professor","profile_url":"https://example.org/alice"}
{"name":"Bob","title":"Professor","profile_url":"https://example.org/bob"}
```
Note that the data in example above is not real, you should replace them with the real data you find.
You should try to find as much information as possible for each faculty members, but if you can't find some information, just leave them empty. Never ever use any fake data like "Unknown University", "No Email", "John Doe", etc.
Note that you can infer the title of the faculty member from the name or your own kownledge about this person if it is not explicitly mentioned.
Note that the data in json block is in jsonl format, which means each line is a json object, and there is no comma between objects. It's not a json array.
""".strip()


RETRIEVE_SCHOLAR_OBJECT = """
Your job is to retrive information of a scholar object from a markdown file.

The markdown file is a resume or profile of a scholar.
You need to extract information from the markdown file and build a Scholar object from what you find.

The definition of the Scholar object is as follows:

```typescript
// The Experience interface represents the experience of a person,
// it can be a education experience, a work experience, a research experience, etc.
interface Experience {
    title: string;  // the title of the experience, e.g. Bachelor, Master, PhD, Postdoc, Professor, Engineer, etc.
    institute: string;  // the name of the institute, e.g. University of Washington, Google, Microsoft, etc.
    department?: string;  // the department of the institute, e.g. Computer Science, Chemistry, etc. Leave it empty if not applicable.
    group?: string;  // the group of the experience, e.g. John's research group, AI4EC Lab, etc. Note that group is different from department, group is more specific, and department is more general. Leave it empty if not applicable.
    advisor?: string;  // the advisor or group leader of the experience, e.g. Prof. John Doe, Dr. Alice, etc. You may infer this from the group name if the advisor is not explicitly mentioned.
    start_year?: number;  // the start year of the experience, e.g. 2010
    end_year?: number; // the end year of the experience, e.g. 2015. If there is only one year is found, in most case its the end year, unless the experience is ongoing, for example, the current job.
    description?: string;  // a brief description of the experience, you can summarize it if it is too long
}

// The Scholar interface represents a scholar, e.g. a professor, an engineer, etc.
interface Scholar {
    name: string;
    title?: string;  // current title of the scholar, e.g. Professor, Associate Professor, Prof, Enginner, etc.
    email?: string;
    goolge_scholar_url?: string; // the url to the google scholar profile of the scholar
    introduction?: string; // a brief introduction of the scholar, you can summarize it if it is too long
    research_domain: string;  // the research domain of the scholar, e.g. Machine Learning, Computer Vision, etc. You can infer this from the description if it is not explicitly mentioned.
    experiences?: Experience[]; // a list of experiences
}
```

You must serialize the Scholar object you find to a json object and put it in a json block, for example:

```json
{"name":"Alice","title":"Associate Professor","email":"alice@example.com","experiences":[{"title":"PhD","institute":"University of Washington", "group":"John's reserach team","advisor":"John Doe","start_year":2010,"end_year":2015,"description":"..."}]}
```
Note that the data in example above is not real, you should replace them with the real data you find.
You should try to find as much information as possible, but if you can't find some information, just leave them empty. Never ever use any fake data like "Unknown University", "No Email", "John Doe", etc.
Note that you should strictly follow the schema of the Scholar object, and the Experience object, and the data type of each field. Don't add any extra fields that are not defined in the schema.
""".strip()


RETRIVE_GROUP_MEMBERS = """
Your job is to retrive information of group members from a markdown file.
The markdown file is a web page about a research group that contain list of group members.

You need to extract information of all group members from the markdown file and build a list of Member objects from what you find. The Member object is defined as the following TypeScript interface:

```typescript
interface Member {
    name: string;
    title?: string;  // the title of the member, e.g. Bachelor, Master, PhD, Postdoc, Professor, Engineer, etc.
    email?: string;
    start_year?: number;  // the start year of the member join the group, e.g. 2010
    is_chinese?: boolean;  // whether the member is Chinese, you can infer this from the name or other information, for example, the name is Chinese pinyin, or the member is from a Chinese institute, etc.
}
```
You must serialize every Member object you find to a single line of json object, aka jsonl format,
and put them in a json block, for example:

```json
{"name":"Alice","title":"PhD","start_year":2010,"description":"...", "is_chinese":false}
{"name":"San Zhang","title":"Master","start_year":2015, "is_chinese":true}
```

Note that the data in example above is not real, you should replace them with the real data you find.
You should try to find as much information as possible for each member, but if you can't find some information, just leave them empty. Never ever use any fake data like "Unknown University", "No Email", "John Doe", etc.
Note that the data in json block is in jsonl format, which means each line is a json object, and there is no comma between objects. It's not a json array.
Note that it is possbile that the markdown page is not a group members page, but a page that contain other information, in this case, you should return an empty json block, for example:
```json
```
Note that you should strictly follow the schema of the Member object, include data type of each field. Don't add any extra fields that are not defined in the schema.
""".strip()