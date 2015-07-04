# Copied from the "MoveText" sublime plugin
# All credit goes to Colin T.A. Gray (colinta)
# https://github.com/colinta/SublimeMoveText
# https://packagecontrol.io/packages/MoveText

from functools import cmp_to_key

from sublime import Region
from sublime_plugin import TextCommand

class MoveTextHorizCommand(TextCommand):
    def move_text_horiz(self, edit, direction):
        for region in self.view.sel():
            if region.empty():
                continue

            orig_region = region
            sel_region = Region(region.begin() + direction, region.end() + direction)

            if sel_region.a < 0 or sel_region.b > self.view.size():
                continue

            if direction < 0:
                dest_region = Region(region.begin() + direction, region.end())
                move_text = self.view.substr(region) + self.view.substr(Region(region.begin() + direction, region.begin()))
            else:
                dest_region = Region(region.begin(), region.end() + direction)
                move_text = self.view.substr(Region(region.end(), region.end() + direction)) + self.view.substr(region)

            # Remove selection from RegionSet
            self.view.sel().subtract(orig_region)
            # Replace the selection with transformed text
            self.view.replace(edit, dest_region, move_text)
            # Add the new selection
            self.view.sel().add(sel_region)

class MoveTextLeftCommand(MoveTextHorizCommand):
    def run(self, edit):
        self.move_text_horiz(edit, -1)

class MoveTextRightCommand(MoveTextHorizCommand):
    def run(self, edit):
        self.move_text_horiz(edit, 1)
