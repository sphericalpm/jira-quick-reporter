# JIRA Quick Reporter

JIRA Quick Reporter (JQR, pronounced "zheeker") is a small desktop application

that helps automate your time management and reporting.

With JQR you can simply manage your issues, workflow, spent time, etc.


### How to build an executable application:
------------
First you should create pyenv based on your system version of python and activate it.

You can find instructions here:

https://github.com/pyenv/pyenv-installer

https://github.com/pyenv/pyenv-virtualenv

Next run ```pip install -r requirements.txt```

Then you should run build_app.py: ```python3 build_app.py```

You can find executable version of JQR in dist/JQR/JQR

### How to work with filters:
-------------
On the main window you can see menu with a list of filters. 
By default you have a 'my open issues' filter and 'Search issues' menu item.

![main window](https://ibb.co/QrQh1Ln)

#### Creating new filter

1. You need to click the 'Search issues' menu item.

2. Then, in the text input you can write a query (default is 'order by created desc').

3. You can click the 'Search' button and see results of the query.

4. To save filter, you need to click the 'Save as' button above the text input.

![main window](https://ibb.co/sC5qNnn)

#### Editing a filter

1. You need to click 'filter_name' menu item.

2. Next you need to follow steps 2-3 from previous paragraph

3. To save edited filter, you need to click the 'Save' button above the text input.
    If you haven't edited a filter, the 'Save' button will be disabled.

#### Syntax help

Queries should be written in JQL.  

Syntax help - https://confluence.atlassian.com/display/JIRASOFTWARECLOUD/Advanced+searching

  

### Contacts
-------------
You can contact us:

Maria Filonova: <mfilonova@spherical.pm>

Dayana Shcheglova: <dshcheglova@spherical.pm>
