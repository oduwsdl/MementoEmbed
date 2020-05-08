from bs4 import BeautifulSoup

def parse_page_metadata(htmltext):

    metadata_list = []

    soup = BeautifulSoup(htmltext, 'html5lib')

    for metatag in soup.find_all('meta'):
        metadata_list.append( metatag.attrs )

    return metadata_list

def find_metaddata_value(metadata_list, attribute, attribute_key=None, attribute_value=None):

    for item in metadata_list:

        if attribute in item:

            if attribute_key is None:
                return item[attribute]

            if item[attribute] == attribute_key:
                
                if attribute_value is not None:

                    if attribute_value in item:
                    
                        return item[attribute_value]

