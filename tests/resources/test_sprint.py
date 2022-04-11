from typing import Iterator, Tuple
from tests.conftest import JiraTestCase, rndstr
from jira.resources import Board, Filter, Sprint
from contextlib import contextmanager


class SprintTests(JiraTestCase):
    def setUp(self):
        super().setUp()
        self.issue_1 = self.test_manager.project_b_issue1
        self.issue_2 = self.test_manager.project_b_issue2
        self.issue_3 = self.test_manager.project_b_issue3

        uniq = rndstr()
        self.board_name = "board-" + uniq
        self.sprint_name = "sprint-" + uniq
        self.filter_name = "filter-" + uniq

        self.board, self.filter = self._create_board_and_filter()

    def tearDown(self) -> None:
        self.board.delete()
        self.filter.delete()  # must do AFTER deleting board referencing the filter
        super().tearDown()

    def _create_board_and_filter(self) -> Tuple[Board, Filter]:
        """Helper method to createa a board and filter"""
        filter = self.jira.create_filter(
            self.filter_name, "description", f"project={self.project_b}", True
        )

        board = self.jira.create_board(
            name=self.board_name, filter_id=filter.id, project_ids=self.project_b
        )
        return board, filter

    @contextmanager
    def _create_sprint(self) -> Iterator[Sprint]:
        """Helper method to create a Sprint."""
        sprint = None
        try:
            sprint = self.jira.create_sprint(self.sprint_name, self.board.id)
            yield sprint
        finally:
            if sprint is not None:
                sprint.delete()

    def test_create_and_delete(self):
        # GIVEN: the board and filter
        # WHEN: we create the sprint
        with self._create_sprint() as sprint:
            sprint = self.jira.create_sprint(self.sprint_name, self.board.id)
            # THEN: we get a sprint with some reasonable defaults
            assert isinstance(sprint.id, int)
            assert sprint.name == self.sprint_name
            assert sprint.state.upper() == "FUTURE"
        # THEN: the sprint .delete() is called successfully

    def test_add_issue_to_sprint(self):
        # GIVEN: The sprint
        with self._create_sprint() as sprint:
            # WHEN: we add an issue to the sprint
            self.jira.add_issues_to_sprint(sprint.id, [self.issue_1])

            sprint_field_name = "Sprint"
            sprint_field_id = [
                f["schema"]["customId"]
                for f in self.jira.fields()
                if f["name"] == sprint_field_name
            ][0]
            sprint_customfield = f"customfield_{sprint_field_id}"

            updated_issue_1 = self.jira.issue(self.issue_1)
            serialised_sprint = getattr(updated_issue_1.fields, sprint_customfield)[0]

            # THEN: We find this sprint in the Sprint field of the Issue
            assert f"[id={sprint.id}," in serialised_sprint
