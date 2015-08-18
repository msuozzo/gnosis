#Gnosis

![An Example Gnosis Template](doc/gnosis_example.png/?raw=true "Example Template")

Gnosis provides an API to record and view information in Google Sheets.

Sheets is a natural choice, not only because of its familiar web interface and
terrific mobile apps, but also because of the quick access to powerful visual
analytics tools. Gnosis leverages this ease of use to allow for dead simple
programmatic access to this data.

##Setup

The spreadsheet example in the screenshot above can be viewed and copied from
[this](https://docs.google.com/spreadsheets/d/1A4-vCOxnW21sRlncRVGX8ZKZzAMnk9SSXmMzQeLbQUY)
address.

Once this is loaded in your google drive,
follow the first 4 steps in
[this](http://gspread.readthedocs.org/en/latest/oauth2.html) guide to set up
your Sheets API access. After doing so, you must 'share' your spreadsheet with
the `client_email` field found in your JSON credential file. 

To use the `Gnosis` class, pass the constructor the following arguments:

* The system path to this JSON credential file
* The `id` of your spreadsheet
    * This `id` is the last portion of the URL to your spreadsheet:
      `https://docs.google.com/spreadsheets/d/`_**`1A4-vCOxnW21sRlncRVGX8ZKZzAMnk9SSXmMzQeLbQUY`**_
