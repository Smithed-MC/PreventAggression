from beet.library.data_pack import Function, FunctionTag
from beet.toolchain.context import Context
import re

call = (
    'execute '
        'if score {key}.major load.status matches {major} '
        'if score {key}.minor load.status matches {minor} '
        'if score {key}.patch load.status matches {patch} '
        'run function {path}'
)

resolve_text = (
    'schedule clear {root}/impl/{version}/technical/tick\n'
    'execute '
        'if score {key}.major load.status matches {major} '
        'if score {key}.minor load.status matches {minor} '
        'if score {key}.patch load.status matches {patch} '
        'run function {root}/calls/{version}/technical/check'
)


enumerate_text = (
    'scoreboard players add {key}.major load.status 0\n'
    'scoreboard players add {key}.minor load.status 0\n'
    'scoreboard players add {key}.patch load.status 0\n'
    'function {root}/calls/{version}/technical/enumerate/major\n'
    'scoreboard players reset {key}.set load.status\n'
)

major_text = (
    'execute '
        'if score {key}.major load.status matches ..{major} '
        'unless score {key}.major load.status matches {major} '
        'run function {root}/calls/{version}/technical/enumerate/set_version\n'
    'execute '
        'if score {key}.major load.status matches ..{major} '
        'if score {key}.major load.status matches {major} '
        'unless score {key}.set load.status matches 1 '
        'run function {root}/calls/{version}/technical/enumerate/minor'
)

minor_text = (
    'execute '
        'if score {key}.minor load.status matches ..{minor} '
        'unless score {key}.minor load.status matches {minor} '
        'run function {root}/calls/{version}/technical/enumerate/set_version\n'
    'execute '
        'if score {key}.minor load.status matches ..{minor} '
        'if score {key}.minor load.status matches {minor} '
        'unless score {key}.set load.status matches 1 '
        'run function {root}/calls/{version}/technical/enumerate/patch'
)

patch_text = (
    'execute '
        'if score {key}.patch load.status matches ..{patch} '
        'unless score {key}.patch load.status matches {patch} '
        'run function {root}/calls/{version}/technical/enumerate/set_version'
)

set_version = (
    'scoreboard players set {key}.major load.status {major}\n'
    'scoreboard players set {key}.minor load.status {minor}\n'
    'scoreboard players set {key}.patch load.status {patch}\n'
    'scoreboard players set {key}.set load.status 1'
)

def make_check(ctx: Context) -> str:
    if('versioning' in ctx.meta):
        meta = ctx.meta['versioning']
        if('dependencies' in meta):
            dependencies = meta['dependencies']
        else:
            dependencies = None
            
        if('log' in meta):
            log = meta['log']
        else:
            log = None
    else:
        return ''
        
    packVersion = ctx.template.globals['version'] = f'v{ctx.project_version}'
    root = meta['root']
    packKey = meta['key']
        
    if(dependencies != None and len(dependencies) > 0):                    

        output = ''
        for i in range(len(dependencies)):
            d = dependencies[i]
            version = d['version']
            split = version.split('.')
            major = split[0]
            minor = split[1]
            patch = split[2]
            key = d['key']
                        
            output += (
                'execute '
                    f'if score {key}.major load.status matches {major} '
                    f'if score {key}.minor load.status matches {minor} '
                    f'if score {key}.patch load.status matches {patch} '
                    f'run scoreboard players add {packKey} load.status 1\n'
            )
            output += (
                'execute '
                    f'unless score {key}.major load.status matches {major} '
                    f'unless score {key}.minor load.status matches {minor} '
                    f'unless score {key}.patch load.status matches {patch} '
                    f'run function ' + f'{root}/calls/{packVersion}/technical/check' + f'/{str(i)}\n'
                    # f'run function ./{str(i)}:\n'
            )
            
            fail_message = f'["Could not find ",{{"text":"{key} {version}","color":"red"}}]'
            fail_text = ''
            
            if(log != None):
                for l in log.splitlines():
                    fail_text += '\t' + l.replace('%s',fail_message) + '\n'
            else:
                fail_text += f'\ttellraw @a {fail_message}'
                
            # output += fail_text

            ctx.data[f'{root}/calls/{packVersion}/technical/check/{str(i)}'] = Function(fail_text)
        output += f'execute if score {packKey} load.status matches ' + str(len(dependencies)) + f' run function {root}/impl/{packVersion}/technical/load\n'
        return output
    else:
        return f'scoreboard players set {packKey} load.status 1\nfunction {root}/impl/{packVersion}/technical/load'

def beet_default(ctx: Context):
    version = ctx.template.globals['version'] = f'v{ctx.project_version}'
    key = ctx.meta['versioning']['key']
    root = ctx.meta['versioning']['root']
    major, minor, patch = version.replace('v', '').split('.')

    yield

    for container in ctx.data["smithed"].values():
        for path in list(container):
            container[path.replace("__version__", version)] = container.pop(path)


    for path in ctx.data.functions.match('impl'):
        first_line = ctx.data.functions[path].text.split('\n')[0]
        if first_line.startswith('#') and '@public' in first_line:
            generate_call(ctx, path, version, root, key)

    ctx.data[f'{root}/calls/{version}/technical/resolve'] = Function(
        resolve_text.format(root=root, key=key, version=version, major=major, minor=minor, patch=patch)
    )

    ctx.data[f'{root}/calls/{version}/technical/check'] = Function(
        make_check(ctx)
    )


    ctx.data[f'{root}/calls/{version}/technical/enumerate'] = Function(
        enumerate_text.format(root=root, key=key, version=version)
    )

    ctx.data[f'{root}/calls/{version}/technical/enumerate/major'] = Function(
        major_text.format(root=root, key=key, version=version, major=major)
    )

    ctx.data[f'{root}/calls/{version}/technical/enumerate/minor'] = Function(
        minor_text.format(root=root, key=key, version=version, minor=minor)
    )

    ctx.data[f'{root}/calls/{version}/technical/enumerate/patch'] = Function(
        patch_text.format(root=root, key=key, version=version, patch=patch)
    )

    ctx.data[f'{root}/calls/{version}/technical/enumerate/set_version'] = Function(
        set_version.format(root=root, key=key, version=version, major=major, minor=minor, patch=patch)
    )
    
    ctx.data[f'{root}/load/enumerate'] = FunctionTag(
        {"values":["{root}/calls/{version}/technical/{tag}".format(root=root, version=version, tag='enumerate')]}
    )
    ctx.data[f'{root}/load/resolve'] = FunctionTag(
        {"values":["{root}/calls/{version}/technical/{tag}".format(root=root, version=version, tag='resolve')]}
    )


def generate_call(ctx, path: str, version: str, root: str, key: str):
    print('  api:', f'#{root}/pub/' + path.split(version)[1][1:])
    major, minor, patch = version.replace('v', '').split('.')

    tag = {
        "values": []
    }

    tag['values'].append(path.replace('impl', 'calls'))

    ctx.data[f'{root}/pub/' + path.split(version)[1][1:]] = FunctionTag(tag)
    ctx.data[path.replace('impl', 'calls')] = Function(call.format(major=major, minor=minor, patch=patch, path=path, key=key))
