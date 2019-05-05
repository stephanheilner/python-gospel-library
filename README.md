# Python Gospel Library

[![Build Status](https://travis-ci.org/CrossWaterBridge/python-gospel-library.svg?branch=master)](https://travis-ci.org/CrossWaterBridge/python-gospel-library)

python-gospel-library parses Gospel Library content.

Typical usage looks like this:

    from gospellibrary.catalogs import CatalogDB
    from gospellibrary.item_packages import ItemPackage

    catalog = CatalogDB(iso639_3_code='eng')

    item = catalog.item(uri='/scriptures/bofm')

    item_package = ItemPackage(item_id=item['id'], item_version=item['version'], iso639_3_code='eng')
    
    item_package.html(subitem_uri='/scriptures/bofm/alma/18', paragraph_id='p27')

Which would give you:

    <p class="verse" data-aid="128350878" id="p27">
        <span class="verse-number">27 </span>And he said, Yea.
    </p>
