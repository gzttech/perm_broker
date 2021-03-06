# coding:utf-8
import six
from ...backend import db
from . import perm_base


def get_or_create_user_perm(user_id):
    user_perm = db.get_inst(db.UserPerm, user_id=user_id, soft_del=False)
    if not user_perm:
        user = db.get_inst(db.User, id=user_id, soft_del=False)
        if not user:
            return None
        user_perm = db.UserPerm(user_id=user_id)
        user_perm.save()
    return user_perm


def add_perm(perm, user_id=None, role_id=None):
    if isinstance(perm, six.string_types):
        perm = perm_base.get_perm_desc_from_string(perm)
    if not perm_base.is_valid_perm_desc(perm):
        return False, "错误的权限描述"
    if user_id:
        user_perm = get_or_create_user_perm(user_id)
        if not user_perm:
            return False, "目标用户不存在"
        if any(map(lambda x: perm_base.equ(perm, x), user_perm.perms)):
            return False, "重复的权限描述"
        user_perm.perms = [*user_perm.perms, perm]
        user_perm.save()
        return True, user_perm
    elif role_id:
        role = db.get_inst(db.RoleDesc, id=role_id)
        if not role:
            return False, "目标角色不存在"
        if any(map(lambda x: perm_base.equ(perm, x), role.perms)):
            return False, "重复的权限描述"
        role.perms = [*role.perms, perm]
        role.save()
        return True, role
    else:
        return False, "用户或者角色id未提供"


def update_perms(perms, user_id=None, role_id=None):
    parsed_perms = []
    for perm in perms:
        if isinstance(perm, six.string_types):
            perm = perm_base.get_perm_desc_from_string(perm)
        if not perm_base.is_valid_perm_desc(perm):
            return False, "错误的权限描述 %s" % perm
        parsed_perms.append(perm)
    if user_id:
        user_perm = get_or_create_user_perm(user_id)
        if not user_perm:
            return False, "目标用户不存在"
        user_perm.perms = parsed_perms
        user_perm.save()
        return True, user_perm
    elif role_id:
        role = db.get_inst(db.RoleDesc, id=role_id)
        if not role:
            return False, "目标角色不存在"
        role.perms = parsed_perms
        role.save()
        return True, role
    else:
        return False, "用户或者角色id未提供"


def remove_perm(perm, user_id=None, role_id=None):
    if isinstance(perm, six.string_types):
        perm = perm_base.get_perm_desc_from_string(perm)
    if not perm_base.is_valid_perm_desc(perm):
        return False, "错误的权限描述"
    if user_id:
        user_perm = get_or_create_user_perm(user_id)
        if not user_perm:
            return False, "目标用户不存在"
        user_perm.perms = list(filter(lambda x: not perm_base.equ(perm, x),
                                      user_perm.perms))
        user_perm.save()
        return True, user_perm
    elif role_id:
        role = db.get_inst(db.RoleDesc, id=role_id, soft_del=False)
        if not role:
            return False, "目标角色不存在"
        role.perms = list(filter(lambda x: not perm_base.equ(perm, x),
                                 role.perms))
        role.save()
        return True, role
    else:
        raise Exception("Neither user_id and role_id is available.")


def get_user_perm_list(user_id, exclude_role=False):
    '''
    获取用户的权限列表.
    user_id: str, 用户的id
    exclude_role: boolean, 是否要排除掉用户的角色中的权限
    '''
    user_perm = db.get_inst(db.UserPerm, user_id=user_id, soft_del=False)
    if not user_perm:
        return []
    else:
        perms = []
        perms.extend(user_perm.perms)
        if (not exclude_role) and user_perm.roles:
            roles = db.get_list_query(db.RoleDesc,
                                      **{'$in': ['id', user_perm.roles],
                                         'soft_del': False})
            for role in roles:
                perms.extend(role.perms)
        return perms


def has_perm(user_id, target_perm_desc,
             is_upstream=False, is_owner=False, perm_list=None):
    '''
    检查用户是否拥有某个指定权限。
    perm_list: list, optional, 如果提供此参数，则不每次调用时根据user_id获取
               用户的权限列表。
    '''
    if isinstance(target_perm_desc, six.string_types):
        target_perm_desc = perm_base\
                .get_perm_desc_from_string(target_perm_desc)
    perm_list = perm_list or get_user_perm_list(user_id)
    if perm_base.is_perm_allowed(perm_list, target_perm_desc,
                                 is_upstream=is_upstream, is_owner=is_owner):
        return True
    #for i in perm_list:
    #    if perm_base.is_perm_matched(i, target_perm_desc,
    #            is_upstream=is_upstream, is_owner=is_owner):
    #        return True
    return False


def get_user_roles(user_id):
    '''
    Return the role objects.
    '''
    user_perm = db.get_inst(db.UserPerm, user_id=user_id, soft_del=False)
    if user_perm and user_perm.roles:
        roles = db.get_list_query(db.RoleDesc,
                                  **{'$in': ['id', user_perm.roles],
                                     'soft_del': False})
        return roles
    return []


def refresh_user_info_roles(user_id, roles):
    user = db.get_inst(db.User, id=user_id)
    if user:
        role_names = []
        if roles:
            role_names = [role_desc.name for role_desc in\
                          db.get_list_query(db.RoleDesc,
                                            **{'$in': ['id', roles],
                                               'soft_del': False})]
        user.info = {**user.info, **{'role_names': role_names}}
        user.save()
        return True
    else:
        return False


def update_user_roles(user_id, role_ids):
    user_perm = get_or_create_user_perm(user_id)
    if not user_perm:
        return False, "用户不存在或已删除"
    role_ids = list(set(role_ids))
    role_count = db.get_list_query(db.RoleDesc,
                                   **{'$in': ['id', role_ids],
                                      'soft_del': False}).count()
    if len(role_ids) != role_count:
        return False, "存在无效的用户角色"
    user_perm.roles = role_ids
    user_perm.save()
    refresh_user_info_roles(user_perm.user_id, user_perm.roles)
    return True, user_perm


def add_role_to_user(role_id, user_id):
    user_perm = get_or_create_user_perm(user_id)
    if not user_perm:
        return False, "用户不存在或已删除"
    role = db.get_inst(db.RoleDesc, id=role_id, soft_del=False)
    if not role:
        return False, "角色不存在或已经删除"
    if not role_id in user_perm.roles:
        user_perm.roles = [*user_perm.roles, role_id]
        user_perm.save()
        refresh_user_info_roles(user_perm.user_id, user_perm.roles)
    return True, user_perm


def remove_role_from_user(role_id, user_id):
    user_perm = get_or_create_user_perm(user_id)
    if not user_perm:
        return False, "用户不存在或已删除"
    user_perm.roles = list(filter(lambda x: x != role_id,
                                  user_perm.roles))
    user_perm.save()
    refresh_user_info_roles(user_perm.user_id, user_perm.roles)
    return True, user_perm


def get_all_roles(soft_del=False):
    roles = db.get_list_query(db.RoleDesc, soft_del=soft_del)
    return list(roles)


def get_role_by_foreign_key(foreign_key):
    if not foreign_key:
        return None
    role_desc = RoleDesc.objects(foreign_key=foreign_key,
                                 soft_del=False).first()
    return role_desc


def create_role(name=None, foreign_key=None):
    if not name:
        return False, "角色名未提供"
    role_desc = db.get_inst(db.RoleDesc, name=name, soft_del=False)
    if role_desc:
        return False, "角色名已经存在"
    role_desc = get_role_by_foreign_key(foreign_key)
    if role_desc:
        return False, "外键已经存在"
    role_desc = db.RoleDesc(name=name, foreign_key=foreign_key)
    role_desc.save()
    return get_role_info(role_desc)


def remove_role(role_id):
    if not role_id:
        return False, "角色id未提供"
    role = db.get_inst(db.RoleDesc, id=role_id)
    if not role:
        return False, "角色不存在"
    role.soft_del = True
    role.save()
    return get_role_info(role)


def update_role(role_id, name=None):
    if not role_id:
        return False, "角色id未提供"
    if not name:
        return False, "名字未提供"
    duplicated_role = db.get_inst(db.RoleDesc,
                                  **{'soft_del': False,
                                     'name': name,
                                     '$ne': ['id', role_id]})
    if duplicated_role:
        return False, "同名角色已经存在"
    role = db.get_inst(db.RoleDesc,
                       id=role_id, soft_del=False)
    if not role:
        return False, "角色不存在"
    role.name = name
    role.save()
    return get_role_info(role)


def get_role_info(role=None, role_id=None, role_name=None):
    if not role:
        if role_id:
            role = db.get_inst(db.RoleDesc, id=role_id)
        elif role_name:
            role = db.get_inst(db.RoleDesc, name=role_name, soft_del=False)
    if not role:
        return False, "角色不存在"
    ret = {'id': str(role.id),
           'name': str(role.name),
           'perms': role.perms,
           'granted_positions': role.granted_positions,
           'foreign_key': role.foreign_key,
           'created': str(role.created),
           'soft_del': role.soft_del,
           'lut': str(role.lut)}
    return True, ret


def get_perm_triples(actions, user_id):
    ret = {}
    perm_list = get_user_perm_list(user_id)
    for action in actions:
        ret.setdefault(action, {})
        ret[action]['*'] = has_perm(user_id, action, perm_list=perm_list)
        ret[action]['+'] = has_perm(user_id, {'action': action, 'effect': 'allow', 'resource': '+'},
                           is_upstream=True, perm_list=perm_list)
        ret[action]['-'] = has_perm(user_id, {'action': action, 'effect': 'allow', 'resource': '-'},
                           is_owner=True, perm_list=perm_list)
    return True, ret
