# script.module.resolveurl

Include the script in your addon.xml

    <requires>
		<import addon="xbmc.python" version="2.1.0"/>
		<import addon="script.module.resolveurl" version="5.0.00"/>
	</requires>

Import ResolveUrl and use it the same as you would with the UrlResolver

    import resolveurl
    resolved = resolveurl.resolve(url)

Or you can import ResolveUrl as UrlResolver to your existing addon that uses the UrlResolver

    import resolveurl as urlresolver
    resolved = urlresolver.resolve(url)

I am in no way responsible for the urls being resolved by 3rd parties. This script only resolves video content from legitimate file lockers without prejudice. If this script is being used by 3rd parties to resolve content that you feel infringes upon your Intellectual Property then please take your complaints to the actual file host and not me. This script in no way searches for any content whatsoever.
