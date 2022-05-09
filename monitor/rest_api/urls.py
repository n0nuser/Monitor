from rest_framework import routers

import rest_api.views as api

# API_TITLE = "Monitor API"
# API_DESCRIPTION = "A Web API for managing agents and metrics."
# schema_view = get_schema_view(title=API_TITLE)

router = routers.DefaultRouter()
router.register(r"agents", api.AgentViewSet)
router.register(r"metrics", api.MetricViewSet)
router.register(r"alerts", api.AlertViewSet)
# router.register(r"schema/", schema_view)
# router.register(r"docs/", include_docs_urls(title=API_TITLE, description=API_DESCRIPTION))
