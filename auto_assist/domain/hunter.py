import requests
from bs4 import BeautifulSoup

class ChemistryHunterCmd:

    def dump_harvard(self, out):
        url = "https://www.chemistry.harvard.edu/faculty"
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        # find all selector: article .node-person

        for person in soup.select('article.node-person'):
            # Example of person
            # <article class="node node-person article with-person-photo modified-in-os_profiles_process_node clearfix" id="node-72151" role="article" target="_top">
            # <div class="field field-name-field-person-photo field-type-imagefield-crop field-label-hidden view-mode-sidebar_teaser">
            # <div class="field-items">
            # <div class="field-item even">
            # <figure>
            # <a href="https://www.chemistry.harvard.edu/people/lu-wang" target="_top"><img alt="Lu Wang" class="image-style-profile-thumbnail" height="75" src="https://www.chemistry.harvard.edu/sites/hwpi.harvard.edu/files/styles/profile_thumbnail/public/chemistry/files/lu_wang_headshot_2023_square.png?m=1688228043&amp;itok=XkHjZTGD" title="Lu Wang" width="75"/></a> </figure>
            # </div>
            # </div>
            # </div>
            # <div class="node-content" ng-non-bindable="">
            # <h1 class="node-title" ng-non-bindable="" rel="nofollow"><a href="https://www.chemistry.harvard.edu/people/lu-wang" target="_top">Lu Wang</a></h1><div class="field field-name-field-professional-title field-type-text field-label-hidden view-mode-sidebar_teaser"><div class="field-items"><div class="field-item even">Assistant Director of Undergraduate Studies</div><div class="field-item odd">Senior Preceptor</div></div></div> </div>
            # </article>

            name = person.select_one('.node-title a').text
            title = person.select_one('.field-name-field-professional-title .field-item').text
            link = person.select_one('.node-title a')['href']
            print(name, title, link)






