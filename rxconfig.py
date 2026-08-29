import reflex as rx
from reflex_base.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="phys_formula",
    db_url="sqlite:///reflex.db",
    plugins=[rx.plugins.RadixThemesPlugin()],
    disable_plugins=[SitemapPlugin],
)
