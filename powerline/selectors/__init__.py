from powerline.theme import layered_selector, recursive_selector

@layered_selector
def mode(target_modes):
    '''Returns True if the current mode to is contained in ``target_mode``

    :param list target_modes:
        The modes to filter.
    '''

    return lambda pl, segment_info, mode: (
        mode in target_mode
    )

@layered_selector
def time(target_start_time, target_end_time):
    '''Returns True if the current time to is between ``target_start_time`` and ``target_end_time``.
    Times are to be specified in the format  . . . (TODO)

    :param string target_start_time:
        The (inclusive) start time.
    :param string target_end_time:
        The (exclusive) end time.
    '''

    #TODO
    return lambda pl, segment_info, mode: (
        True
    )

@layered_selector
@recursive_selector
def all_of(**kwargs):
    '''Checks whether all of the given conditions are satisfied

    :param args condition:
        Any argument passed to this selector will be interpreted as a selector on its own that may have arguments.
    '''

    return lambda pl, segment_info, mode: (
        all([func(pl=pl, segment_info=segment_info, mode=mode) for arg, func in kwargs.items() if func])
    )

@layered_selector
@recursive_selector
def any_of(**kwargs):
    '''Checks whether any of the given conditions are satisfied

    :param kwargs condition:
        Any argument passed to this selector will be interpreted as a selector on its own that may have arguments.
    '''

    return lambda pl, segment_info, mode: (
        any([func(pl=pl, segment_info=segment_info, mode=mode) for arg, func in kwargs.items() if func])
    )
