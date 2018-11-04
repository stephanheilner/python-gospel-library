# Python Gospel Library

[![Build Status](https://travis-ci.org/CrossWaterBridge/python-gospel-library.svg?branch=master)](https://travis-ci.org/CrossWaterBridge/python-gospel-library)

python-gospel-library parses Gospel Library content.

Typical usage looks like this:

    from gospellibrary.catalogs import CatalogDB
    from gospellibrary.item_packages import ItemPackage

    catalog = CatalogDB()

    item = catalog.item(uri='/scriptures/bofm', lang='eng')

    item_package = ItemPackage(item_external_id=item['external_id'], item_version=item['version'])
    
    item_package.html(subitem_uri='/scriptures/bofm/alma/18', paragraph_id='p27')

Which would give you:

    <p class="verse" data-aid="128350878" id="p27">
        <span class="verse-number">27 </span>And he said, Yea.
    </p>
