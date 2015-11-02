# Python Gospel Library

[![Build Status](https://travis-ci.org/CrossWaterBridge/python-gospel-library.svg?branch=master)](https://travis-ci.org/CrossWaterBridge/python-gospel-library)

python-gospel-library parses Gospel Library content.

Typical usage looks like this:

    from gospellibrary.catalogs import CatalogDB
    from gospellibrary.item_packages import ItemPackage
    
    catalog = CatalogDB()
    
    item = catalog.item(uri="/scriptures/bofm", lang="eng")
    
    item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['latest_version'])
    
    item_package.html(uri="/scriptures/bofm/alma/18.27")

Which would give you:

    <p class="verse" uri="/scriptures/bofm/alma/18.27" pid="fx0O72LQTEy0qOQn1Egaaw" hash="fFzuKQ">
        <span class="verseNumber">27</span>And he said, Yea.
    </p>
