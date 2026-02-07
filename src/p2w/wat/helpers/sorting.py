"""WAT helper functions: Sorting functions."""

from __future__ import annotations

SORTING_CODE = """

;; sorted(iterable, key=func) - returns new sorted list using key function
(func $sorted_with_key (param $iterable (ref null eq)) (param $key_fn (ref null eq)) (result (ref null eq))
  (local $result (ref null eq))
  ;; Copy the list first
  (local.set $result (call $copy_list (local.get $iterable)))
  ;; Sort with key function
  (call $list_sort_with_key (local.get $result) (local.get $key_fn))
)

"""
