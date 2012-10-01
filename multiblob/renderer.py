import contextlib
import functools
import weakref

import pyglet

from multiblob import datastructures

class Renderer(object):
    """A component, that can renders aspects of the game state."""

    def render(self, game_state):
        """Render some aspect of the game state. Override this in subclasses."""
        pass

class ManagedBatch(pyglet.graphics.Batch):
    class DefaultKey(object):
        pass

    def __init__(self, *args, **kwargs):
        pyglet.graphics.Batch.__init__(self, *args, **kwargs)

        self._vertex_lists = datastructures.MultiDict()
        self._default_key = self.DefaultKey

    def set_default_key(self, key):
        """Sets the default key to use for `add` operations."""
        self._default_key = key

    @contextlib.contextmanager
    def use_key(self, key):
        """Generator to use in a with block to temporarily set the key."""
        old_key = self._default_key
        self._default_key = key
        yield
        self._default_key = old_key

    def _clean_vertex_list(self, list_key_ref):
        self.remove_key_ref(list_key_ref)

    def _wrap_vertex_list(self, vertex_list):
        d = vertex_list.delete
        @functools.wraps(d)
        def delete_wrapper(notify=True):
            try:
                d()
            except AssertionError:
                pass
            if notify:
                self.remove_vertex_list(vertex_list)
        vertex_list.delete = delete_wrapper
        return vertex_list
    
    def get(self, list_key):
        """Returns the vertex lists tracked using the given `list_key`."""
        return self._vertex_lists.getlist(self.get_key_ref(list_key))

    def set(self, list_key, *args, **kwargs):
        """Add a vertex list as with Batch.add and track it using the given
        `list_key`."""
        vertex_list = self._wrap_vertex_list(pyglet.graphics.Batch.add(
                self, 
                *args, 
                **kwargs
                ))
        self._vertex_lists.setlistdefault(
                self.get_key_ref(list_key),
                []
                ).append(vertex_list)
        return vertex_list

    def set_indexed(self, list_key, *args, **kwargs):
        """Add an indexed vertex list as with Batch.add_indexed and track it
        using the given `list_key`."""
        vertex_list = self._wrap_vertex_list(pyglet.graphics.Batch.add_indexed(
                self, 
                *args, 
                **kwargs
                ))
        self._vertex_lists.setlistdefault(
                self.get_key_ref(list_key),
                []
                ).append(vertex_list)
        return vertex_list

    def add(self, *args, **kwargs):
        return self.set(self._default_key, *args, **kwargs)

    def add_indexed(self, *args, **kwargs):
        return self.set_indexed(self._default_key, *args, **kwargs)

    def remove(self, list_key):
        """Remove a vertex list with the given `list_key`. Also calls
        `VertexList.delete`."""
        self.remove_key_ref(self.get_key_ref(list_key))

    def get_key_ref(self, key):
        try:
            return weakref.ref(key, self._clean_vertex_list)
        except TypeError:
            return key

    def remove_key_ref(self, list_key_ref):
        for vertex_list in self._vertex_lists.getlist(list_key_ref):
            try:
                vertex_list.delete(notify=False)
            except UnboundLocalError:
                pass
        del self._vertex_lists[list_key_ref]

    def remove_vertex_list(self, vertex_list):
        for list_key_ref, vertex_lists in self._vertex_lists.lists():
            if vertex_lists in vertex_lists:
                self._vertex_lists.setlistdefault(list_key_ref).remove(vertex_list)

    def clear(self, keep_keys=[]):
        """Delete all vertex lists except the ones in `keep_keys`. Returns a
        list of keys whose vertex lists have been deleted."""
        removed = []
        for list_key_ref in self._vertex_lists.keys():
            list_key = list_key_ref()
            if list_key is None or list_key not in keep_keys:
                self.remove(list_key)
                removed.append(list_key)
        return removed

    def migrate(self, vertex_list, mode, group, batch):
        pyglet.graphics.Batch.migrate(self, vertex_list, mode, group, batch)
        if not batch is self:
            for list_key_ref, other_vertex_lists in self._vertex_lists.lists():
                if vertex_list in other_vertex_lists:
                    self._vertex_lists.setlistdefault(list_key_ref).remove(vertex_list)

    def __contains__(self, list_key):
        return self.get_key_ref(list_key) in self._vertex_lists
