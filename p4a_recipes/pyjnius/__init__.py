# In p4a_recipes/pyjnius/__init__.py

from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.toolchain import shprint, current_directory, info
from pythonforandroid.patching import will_build, apply_patch # Keep apply_patch import
import sh
from os.path import join, dirname, exists # Import 'exists'

class PyjniusRecipe(CythonRecipe):
    version = '1.6.1'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.zip'
    name = 'pyjnius'
    depends = [('genericndkbuild', 'sdl2'), 'six']
    site_packages_name = 'jnius'

    # Keep this patches list for p4a's internal logic,
    # but we'll manually apply our specific patch for debug/forcing.
    patches = [
        ('genericndkbuild_jnienv_getter.patch', will_build('genericndkbuild')),
        ('pyjnuis_long_fix.patch', None)
    ]

    def build_arch(self, arch):
        # Call the parent build_arch first. This will handle downloading,
        # extracting, and running other default p4a logic, including its own
        # patch application (which we've seen isn't working for our specific patch).
        super().build_arch(arch)

        # --- DEBUG: Manually apply the pyjnuis_long_fix.patch here ---
        info('DEBUG: Attempting to manually apply pyjnuis_long_fix.patch...')
        
        # Construct the full path to your patch file
        patch_file_path = join(dirname(__file__), 'patches', 'pyjnuis_long_fix.patch')
        
        # Get the build directory for the current architecture
        build_dir = self.get_build_dir(arch.arch)
        
        # Construct the full path to the file that needs patching
        target_file_path = join(build_dir, 'jnius', 'jnius_utils.pxi')

        # Basic checks before patching
        if not exists(patch_file_path):
            info(f'ERROR: Patch file not found: {patch_file_path}')
            raise FileNotFoundError(f'Patch file not found: {patch_file_path}')
        
        if not exists(target_file_path):
            info(f'ERROR: Target file not found for patching: {target_file_path}')
            raise FileNotFoundError(f'Target file not found: {target_file_path}')
            
        # Change to the build directory before running patch, as patch -p1 expects
        # to be run from the root of the source tree.
        with current_directory(build_dir):
            try:
                # -p1 removes one leading directory component (e.g., 'a/' or 'b/')
                # -i specifies the input patch file
                # _env=self.get_recipe_env(arch) ensures patch runs with correct environment vars
                shprint(sh.patch, '-p1', '-i', patch_file_path, _env=self.get_recipe_env(arch))
                info('DEBUG: pyjnuis_long_fix.patch applied successfully via manual call.')
            except sh.ErrorReturnCode as e:
                # If patch fails, print its output and re-raise the exception
                info(f'DEBUG: Manual patch application FAILED for {target_file_path}:')
                info(f'STDOUT: {e.stdout.decode("utf-8", errors="ignore")}')
                info(f'STDERR: {e.stderr.decode("utf-8", errors="ignore")}')
                raise # Re-raise to stop the build and show the error

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # NDKPLATFORM is our switch for detecting Android platform, so can't be None
        env['NDKPLATFORM'] = "NOTNONE"
        return env

    def postbuild_arch(self, arch):
        super().postbuild_arch(arch)
        info('Copying pyjnius java class to classes build dir')
        with current_directory(self.get_build_dir(arch.arch)):
            shprint(sh.cp, '-a', join('jnius', 'src', 'org'), self.ctx.javaclass_dir)

recipe = PyjniusRecipe()
