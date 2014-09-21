import scraperwiki
import httplib2
from lxml.html import fromstring, tostring
import lxml.cssselect
from pprint import pprint
import urllib
import re
import datetime


TABLE = 'linebudgets'

today = datetime.date.today()

id_matcher = re.compile(r'\d\d[A-Z]\d\d\d')
cleanup_re = re.compile('[^a-zA-Z0-9_]')

def normalize_key(key):
    key = '_'.join(key.lower().strip().split())
    key = cleanup_re.sub('', key)
    return key


# Derive major categories from thousands of categories (needs to be expanded)
# Not using a dict b/c we might care about the order of matching.
category_map = (
    ('snapple', re.compile(r"snapple", re.IGNORECASE)),
    ("private", re.compile(r"private", re.IGNORECASE)),
    ("tl", re.compile(r"^tl", re.IGNORECASE)),
    ("title N", re.compile(r"^(title [ivx]+)\b", re.IGNORECASE)),
    ("prek", re.compile(r"pre.?k", re.IGNORECASE)),
)


def scrape(schoolcode):

    # New system with slightly different markup debuted 2010,
    # and markup changed again in 2011.
    
    base_uri = "http://schools.nyc.gov/AboutUs/funding/schoolbudgets/FY14FairStudentFundingBudget.htm"
    params = {'schoolcode': schoolcode}
    params = urllib.urlencode(params)
    uri = base_uri + '?' + params
    #print "Fetching %s" % uri
    # Hooray, they have a bad SSL certificate. Ignore it.
    ##h = httplib2.Http(disable_ssl_certificate_validation=True)
    ##response, text = h.request(uri)
    ##assert response.status == 200
    try:
        text = scraperwiki.scrape(uri)
    except urllib2.HTTPError, e:
        print "Page not loaded, error %s" % e.getcode()
        return

    tree = fromstring(text)
    if tree.cssselect("div.notfound"):
        print "Not found", uri
        return
    if re.search("Budget Allocation Not Found.|School .... not found.", text):
        print "Not found", uri
        return

    #budget_rows = tree.cssselect('table.budget-ra budget-ra-top-bottom tr')
    school_name = tree.cssselect('div.schoolname a')
    print school_name[0].text_content().encode("utf-8")
    ell_budget = tree.cssselect('span#doecontrol_bottomcentercontainer_School_Budget_Overview_lblELLSubTotal_C04')
    print ell_budget[0].text_content().encode("utf-8")
    #school_name = school_name
    #print school_name
    output = {'school_id': schoolcode, 'school_name':school_name }

    # sometimes there's a header, sometimes not
   # if re.search('Data Source GALAXY|Allocation CategoryFY[\s\xa0]*\d\d\d\d', budget_rows[0].text_content()):
     ##   del budget_rows[0]
    #catmap = { }
   # for table_row in budget_rows: 
    #    cells = table_row.cssselect('td')
    #    if len(cells) != 2:
    #        continue
    #    if not cells[0].text or not cells[1].text:
       #     continue
#
      #  category = cells[0].text.strip()
     #   #category not in catmap, (category, catmap)
       # catmap[category] = cells[1].text.strip()

    ldata = [ ]
    data["dollars"] = ell_budget;
    #for category, val in catmap.items():
        #data = { "category":category, "val":val }
     #   eif re.match("[\d\$.]+$", val[0]):
       #     data["dollars"] = int(re.sub("[\$,]", "", val))
        #else:
        #    assert val == "TBD", data

        #data['majorcategory'] = 'unknown'
       # for majorcat, regex in category_map:
       #     matched = regex.search(category)
         #   if matched:
          #      if len(matched.groups()):
         #            majorcat = matched.group(1).lower()
         #       data['majorcategory'] = majorcat
         #       break

    data.update(output)
    ldata.append(data)

    #pprint(ldata)
    scraperwiki.sqlite.save(unique_keys=['school_id'], data=ldata, table_name=TABLE)


def get_school_ids():
    uri = 'http://schools.nyc.gov/NR/rdonlyres/25DC86E5-BBE0-4E0C-8F8A-05B954B99238/0/2010_2011_All_ProgressReportResults_2011_11_10.xlsx'
    #data = scraperwiki.scrape(uri)
    h = httplib2.Http() #disable_ssl_certificate_validation=True)
    nope, data = h.request(uri)
    import openpyxl
    import StringIO
    file_obj = StringIO.StringIO()
    file_obj.write(data)
    file_obj.seek(0)
    wb = openpyxl.load_workbook(file_obj)
    sheet = wb.get_sheet_by_name('2010-11 Progress Report Results')
    rows = sheet.range('B1:B9999')
    for i, row in enumerate(rows):
        if i < 0:
            continue
        cell = row[0]
        if not cell.value:
            continue
        if id_matcher.match(cell.value):
            # Ignore the first two digits, don't know what those are.
            # District maybe?
            yield cell.value[2:]


def main(reset=False, first_code="X334"):
    import time
    start = time.time()
    codes = list(get_school_ids())
    #print "Got %d school ids..." % len(codes)
   
    #for i, schoolcode in enumerate(codes):
        #if first_code is not None:
            #if schoolcode == first_code:
                #print "Starting with", schoolcode
                #first_code = None
            #else:
                #continue
    try:
        #print "doing school", i + 1, "of", len(codes), "with id", first_code
        print "doing school", 1, "of", len(codes), "with id", first_code
        scrape(first_code)
    except Exception as e:
        print "Unhandled exception on school %s" % (first_code)
        import traceback
        print traceback.format_exc()
    print "Ran in %s seconds" % (time.time() - start)



# Can't really handle more than 1 year per run, scraperwiki kills it.
main()  #reset=False, years=[2006])



