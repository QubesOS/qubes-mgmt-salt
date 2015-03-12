# -*- coding: utf-8 -*-`
#
# vim: set ts=4 sw=4 sts=4 et :


class DictDiffer(object):
    """A dictionary difference calculator.

    Originally posted as:
    http://stackoverflow.com/questions/1165352/fast-comparison-between-two-python-dictionary/1165552#1165552

    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.current_keys, self.past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
        ]
        self.intersect = self.current_keys.intersection(self.past_keys)

    def added(self):
        return self.current_keys - self.intersect
    def removed(self):
        return self.past_keys - self.intersect
    def changed(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] == self.current_dict[o])


class ListDifferOrig(object):
    """A list difference calculator.

    Calculate the difference between two lists as:
    (1) items added
    (2) items removed
    (3) items same in both
    """
    def __init__(self, current_list, past_list):
        self.current_list, self.past_list = current_list, past_list
    def added(self):
        return [item for item in self.current_list if item not in self.past_list]
    def removed(self):
        return [item for item in self.past_list if item not in self.current_list]
    def unchanged(self):
        return [item for item in self.current_list if item in self.past_list]


class ListDiffer(object):
    """A list difference calculator.
    """
    def __init__(self, current_list, past_list):
        self.current_list, self.past_list = current_list, past_list

        try:
            self.current_set = set((current_list))
            self.past_set = set((past_list))
        except TypeError:
            self.current_set = set(map(tuple, current_list))
            self.past_set = set(map(tuple, past_list))

    def diff(self):
        '''symetric_differences lists ALL differences; both added and removed
        '''
        return self.current_set.symmetric_difference(self.past_set)

    def common(self):
        '''Contain elements that are in both; all common, added and removed
        '''
        return self.current_set.union(self.past_set)

    def added(self):
        '''Lists differences only; in this case will list all new elements in current_set
        '''
        return self.current_set.difference(self.past_set)

    def removed(self):
        '''Lists differences only; in this case will list all removed items from past_set
        '''
        return self.past_set.difference(self.current_set)

    def unchanged(self):
        '''Contains elements common to both; in this case will list unchanged elements
        '''
        return self.current_set.intersection(self.past_set)


