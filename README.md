# Python Gospel Library

[![Build Status](https://travis-ci.org/LDSMobileApps/python-gospel-library.svg?branch=master)](https://travis-ci.org/LDSMobileApps/python-gospel-library)

python-gospel-library parses Gospel Library content.

Typical usage looks like this:

    from gospellibrary import Catalog
    
    catalog = Catalog()
    
    item = catalog.item(uri="/scriptures/bofm", lang="eng")
    
    with item.package() as package:
        package.html(uri="/scriptures/bofm/alma/18.27")

Which would give you:

    <p class="verse" uri="/scriptures/bofm/alma/18.27" pid="fx0O72LQTEy0qOQn1Egaaw" hash="fFzuKQ">
        <span class="verseNumber">27</span>And he said, Yea.
    </p>
