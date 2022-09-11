from __future__ import unicode_literals

import typing as t

import renpy

from script_jump.utils import removeprefix, NodeWrapper

__all__ = ("node_text", )


def node_text(node_wrapper):
    # type: (NodeWrapper) -> t.Text
    """Get the text on the first line for the node in `node_wrapper`."""
    try:
        return _type_to_decode_func[type(node_wrapper.node)](node_wrapper)
    except KeyError:
        return "<type: {}>".format(type(node_wrapper.node).__name__)


def _double_quoted_repr(string):
    return (
        repr("'" + string.replace('"', "\U00101111"))
        .replace("\\U00101111", '\\"')
        .replace("'", "", 1)
    )


def _get_args_string(arguments):
    # type: (renpy.ast.ArgumentInfo) -> t.Text
    args = []
    for arg_pos, (name, argument) in enumerate(arguments.arguments):
        if name is None:
            if arg_pos in arguments.starred_indexes:
                argument = "*" + argument
            elif arg_pos in arguments.doublestarred_indexes:
                argument = "**" + argument
            args.append(argument)
        else:
            args.append("{}={}".format(name, argument))
    return "({})".format(", ".join(args))


def _format_param_with_default(name, default):
    # type: (t.Text, t.Text | None) -> t.Text
    if default is not None:
        return "{}={}".format(name, default)
    else:
        return "{}".format(name)


def _get_params_string(parameters):
    # type: (renpy.ast.ParameterInfo) -> t.Text
    parts = []

    if parameters.positional_only:
        for param_name, default in parameters.positional_only:
            parts.append(_format_param_with_default(param_name, default))
        parts.append("/")

    for param_name, default in parameters.parameters[len(parameters.positional_only):len(parameters.positional)]:
        parts.append(_format_param_with_default(param_name, default))

    if parameters.extrapos is not None:
        parts.append("*{}".format(parameters.extrapos))

    if parameters.keyword_only:
        if parameters.extrapos is None:
            parts.append("*")
        for param_name, default in parameters.keyword_only:
            parts.append(_format_param_with_default(param_name, default))

    if parameters.extrakw is not None:
        parts.append("**{}".format(parameters.extrakw))

    return "({})".format(", ".join(parts))


def _get_imspec_string(imspec):
    # type: (tuple[tuple[str, ...], str | None, str | None, list[str], str | None, str | None, list[str]] | tuple[tuple[str, ...], str | None, str | None, list[str], str | None, str | None] | tuple[tuple[str, ...], list[str], str | None]) -> t.Text
    if len(imspec) == 7:
        name, expression, tag, at_expr_list, layer, zorder, behind = imspec
    elif len(imspec) == 6:
        name, expression, tag, at_expr_list, layer, zorder, = imspec
        behind = []
    else:
        name, at_expr_list, layer = imspec
        tag = expression = zorder = None
        behind = []
    parts = []
    if expression is not None:
        parts.append("expression {}".format(expression))
    else:
        parts.append(" ".join(name))

    if tag is not None:
        parts.append("as {}".format(tag))

    if at_expr_list:
        parts.append("at {}".format(", ".join(at_expr_list)))

    if layer is not None:
        parts.append("onlayer {}".format(layer))

    if zorder is not None:
        parts.append("zorder {}".format(zorder))

    if behind:
        parts.append("behind {}". format(", ".join(behind)))

    return " ".join(parts)


def _decode_say(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Say]) -> t.Text
    """Decode the Say node `node` into the statement that creates it."""
    node = node_wrapper.node
    parts = []
    if node.who:
        parts.append(node.who)

    if node.attributes is not None:
        parts.extend(node.attributes)

    if node.temporary_attributes is not None:
        parts.append("@")
        parts.extend(node.temporary_attributes)

    parts.append(_double_quoted_repr(node.what))

    if node.with_:
        parts.append("with")
        parts.append(node.with_)

    if node.arguments:
        parts.append(_get_args_string(node.arguments))

    if hasattr(node, "identifier"):
        parts.append("id")
        parts.append(node.identifier)

    if not node.interact:
        parts.append("nointeract")

    return " ".join(parts)


def _decode_scene(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Scene]) -> t.Text
    node = node_wrapper.node

    if node.imspec is None:
        return "scene onlayer {}".format(node.layer)
    else:
        parts = ["scene", _get_imspec_string(node.imspec)]

    if (
            node_wrapper.previous_wrapper is not None
            and getattr(node_wrapper.previous_wrapper.node, "paired") is not None
    ):
        parts.append("with {}".format(node_wrapper.previous_wrapper.node.paired))

    return_string = " ".join(parts)
    if node.atl is not None:
        return_string += ":"

    return return_string


def _decode_show(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Show]) -> t.Text
    node = node_wrapper.node
    parts = ["show", _get_imspec_string(node.imspec)]

    if (
            node_wrapper.previous_wrapper is not None
            and getattr(node_wrapper.previous_wrapper.node, "paired") is not None
    ):
        parts.append("with {}".format(node_wrapper.previous_wrapper.node.paired))

    return_string = " ".join(parts)
    if node.atl is not None:
        return_string += ":"

    return return_string


def _decode_show_layer(node_wrapper):
    # type: (NodeWrapper[renpy.ast.ShowLayer]) -> t.Text
    node = node_wrapper.node
    parts = ["show layer {}".format(node.layer)]
    if node.at_list:
        parts.append("at {}".format(", ".join(node.at_list)))

    return_string = " ".join(parts)
    if node.atl is not None:
        return_string += ":"

    return return_string


def _decode_hide(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Hide]) -> t.Text
    parts = ["hide", _get_imspec_string(node_wrapper.node.imspec)]
    if (
            node_wrapper.previous_wrapper is not None
            and getattr(node_wrapper.previous_wrapper.node, "paired") is not None
    ):
        parts.append("with {}".format(node_wrapper.previous_wrapper.node.paired))
    return " ".join(parts)


def _decode_camera(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Camera]) -> t.Text
    node = node_wrapper.node
    parts = ["camera"]
    if node.layer != "master":
        parts.append(node.layer)
    if node.at_list:
        parts.append("at {}".format(", ".join(node.at_list)))

    return_string = " ".join(parts)
    if node.atl is not None:
        return_string += ":"

    return return_string


def _decode_jump(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Jump]) -> t.Text
    node = node_wrapper.node
    parts = ["jump"]
    if node.expression:
        parts.append("expression")
    parts.append(node.target)
    return " ".join(parts)


def _decode_call(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Call]) -> t.Text
    node = node_wrapper.node
    parts = ["call"]
    if node.expression:
        parts.append("expression")
    parts.append(node.label)
    if node.arguments is not None:
        parts.append(_get_args_string(node.arguments))
    return " ".join(parts)


def _decode_python(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Python]) -> t.Text
    node = node_wrapper.node

    if not node.code.source.startswith("\n"):
        return "$ {}".format(node.code.source)

    parts = ["python"]
    if node.hide:
        parts.append("hide")
    if node.store != "store":
        parts.append("in {}".format(removeprefix(node.store, "store.")))

    return " ".join(parts) + ":"


def _decode_with(node_wrapper):
    # type: (NodeWrapper[renpy.ast.With]) -> t.Text
    node = node_wrapper.node
    if node.paired is not None:
        return "with {} <paired below>".format(node.paired)
    return "with {}".format(node_wrapper.node.expr)


def _decode_label(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Label]) -> t.Text
    node = node_wrapper.node
    param_string = _get_params_string(node.parameters) if node.parameters is not None else ""
    parts = ["label {}{}".format(node.name, param_string)]

    if node.hide:
        parts.append("hide")

    return " ".join(parts) + ":"


def _decode_if(node_wrapper):
    # type: (NodeWrapper[renpy.ast.If]) -> t.Text
    return "if {}:".format(node_wrapper.node.entries[0][0])


def _decode_while(node_wrapper):
    # type: (NodeWrapper[renpy.ast.While]) -> t.Text
    return "while {}:".format(node_wrapper.node.condition)


def _decode_pass(_node_wrapper):
    # type: (NodeWrapper[renpy.ast.Pass]) -> t.Text
    return "pass"


def _decode_return(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Return]) -> t.Text
    return "return {}".format(node_wrapper.node.expression)


def _decode_menu(node_wrapper):
    # type: (NodeWrapper[renpy.ast.Menu]) -> t.Text
    node = node_wrapper.node
    args_string = _get_args_string(node.arguments) if node.arguments is not None else ""
    return "menu{}:".format(args_string)


def _decode_user_statement(node_wrapper):
    # type: (NodeWrapper[renpy.ast.UserStatement]) -> t.Text
    return node_wrapper.node.line


_type_to_decode_func = {
    renpy.ast.Say: _decode_say,
    renpy.ast.Scene: _decode_scene,
    renpy.ast.Show: _decode_show,
    renpy.ast.ShowLayer: _decode_show_layer,
    renpy.ast.Hide: _decode_scene,
    renpy.ast.Camera: _decode_camera,
    renpy.ast.Jump: _decode_jump,
    renpy.ast.Call: _decode_call,
    renpy.ast.Python: _decode_python,
    renpy.ast.With: _decode_with,
    renpy.ast.Label: _decode_label,
    renpy.ast.If: _decode_if,
    renpy.ast.While: _decode_while,
    renpy.ast.Pass: _decode_pass,
    renpy.ast.Return: _decode_return,
    renpy.ast.Menu: _decode_menu,
    renpy.ast.UserStatement: _decode_user_statement,
}
