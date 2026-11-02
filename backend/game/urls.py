from django.urls import path
from . import views
urlpatterns=[path("health/",views.health),path("wallet/",views.wallet),path("seeds/current/",views.current_seed),path("seeds/client/",views.set_client_seed),path("seeds/rotate/",views.rotate_seed),path("games/dice/play/",views.dice_play),path("games/crash/play/",views.crash_play),path("games/plinko/play/",views.plinko_play),path("games/history/",views.history),path("fairness/verify/",views.verify_round),path("fairness/rounds/<int:round_id>/",views.round_detail)]
