<%inherit file="splash_base.mako" />

<%block name="additional_css">
    .faq li {
        margin:10px 0;
    }

    .polymathian {
        margin:30px 0;
    }
</%block>

<%block name="header_title">Facility Location Optimisation</%block>

<%block name="app_description">
    <p>Do you have to manage a hub and spoke supply chain? Are you thinking of repositioning your hubs, introducing a new hub and want to
    determine it's catchment, or just want to know how good your current hub locations are?</p>
    <p>Do you have depot locations for staff which service a large geographic area? Are you thinking of relocating or building a new depot?</p>
    <p>Are you looking to install telecommunications equipment? Want to determine the optimal location to minimise overall traffic distance?</p>
    <p>Are you looking to design territories for salesman? Bringing on a new salesman and want to determine how the new catchments will stack up?</p>
    <p>Want to view the answer on a map, and download it as a KML file to share with colleagues?</p>
    <p>This app might be what you are looking for! Sign up and give it a go.
    <p>Need help or wish this app had more features, contact us at <b>info@tropofy.com</b> to see if we can help</p>
</%block>

## Body
<div class="row">
    <div class="col-sm-6">
        <h3 class="text-center">Input Data</h3>
        <p>Enter the locations which have to be serviced i.e. shops that need product, locations to which staff have to travel or nodes for communications traffic.</p>
        <p>Enter the set of locations that can act as hubs i.e. new and/or existing depot locations, new installation locations, salesman base locations.</p>
    </div>

    <div class="col-sm-6">
        <h3 class="text-center">Output Data</h3>
        <p>See the optimal catchment for each chosen hub location as a list of hubbees and view it on a map</p>
    </div>
</div>

<div class="row"></div>

<div class="row">
    <div class="col-xs-12">
        <div class="polymathian text-center">
        This app was created using the <a href="http://www.tropofy.com" target="_blank">Tropofy platform</a>.
        </div>
    </div>
</div>
