# auto-assist

Collection of automation tools for various tasks.

## Usage

### Lauch a browser interactively
Use this to manually setup the browser before running other tasks. For example, login to websites, etc.
```bash
poetry run python -m auto_assist.main browser launch
```

### Search Google Scholar by authors
```bash
cat authors.txt | poetry run python -m auto_assist.main task gs_search_by_authors --keyword chemistry
```

### Extract Google Scholar profile URLs from search result
```bash
poetry run python -m auto_assist.main task gs_list_profile_urls gs_result.jsonl > gs_profiles.txt
```

### Crawling Google Scholar profiles from search results
```bash
cat gs_profiles.txt | poetry run python -m auto_assist.main task gs_explore_profiles 
```