from datetime import date

from test_email_recovery import auth_db


def test_api_month_defaults_to_current_season_even_without_future_filter(auth_db, monkeypatch):
    from api.routers import tournaments as routes
    from models import Tournament
    _, factory, User = auth_db
    monkeypatch.setattr(routes, 'get_active_tournament_date_range', lambda: (date(2026,8,1), date(2027,6,30)))
    with factory() as db:
        for idx, day in enumerate([date(2025,11,20),date(2026,11,20),date(2027,1,20),date(2027,11,20)],1):
            db.add(Tournament(tournament_id=idx,month='Ноябрь' if day.month==11 else 'Январь',date=day,name='Фестиваль'))
        db.commit()
        def listed(month=None,season=None):
            return routes.list_tournaments(month=month,future_only=False,from_date=None,to_date=None,search=None,my_approved_only=False,
                                           season=season,db=db,user=db.get(User,123))
        assert [r['tournament_id'] for r in listed('Ноябрь')]==[2]
        assert [r['tournament_id'] for r in listed()]==[2,3]
        assert [r['tournament_id'] for r in listed('Ноябрь','2025-2026')]==[1]
        assert len(listed(season='all'))==4
        assert db.query(Tournament).count()==4


def test_active_season_guard_boundaries(monkeypatch):
    from utils import season
    monkeypatch.setattr(season,'get_today',lambda:date(2026,11,14))
    assert not season.is_active_tournament_date(date(2025,11,20))
    assert not season.is_active_tournament_date(date(2026,7,31))
    assert season.is_active_tournament_date(date(2026,8,1))
    assert season.is_active_tournament_date(date(2027,6,30))
    assert not season.is_active_tournament_date(date(2027,7,1))
