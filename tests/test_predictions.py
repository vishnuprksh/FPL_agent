from fpl_agent.predictions import update_player_predictions


def test_predictions():
    results = update_player_predictions()

    # At minimum, the function should return a list (possibly empty) and each item should have keys
    assert isinstance(results, list)
    for item in results[:5]:
        assert 'player_id' in item
        assert 'pred_match1' in item
        assert 'total_pred' in item


if __name__ == "__main__":
    test_predictions()