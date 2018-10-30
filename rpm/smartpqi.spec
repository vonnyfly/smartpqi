%define kmod_name		smartpqi
%define kmod_driver_version	1.1.5
%define kmod_rpm_release	1
%define kmod_kbuild_dir		kernel/linux/smartpqi
%define kmod_kernel_version     %{?kernel_version:%{kernel_version}}%{!?kernel_version:%{latest_kernel}}

%{!?dist: %define dist .el6}

Source0:	%{kmod_name}-%{kmod_driver_version}.tar
Source1:	%{kmod_name}.files
Source2:	depmodconf
Source3:	find-requires.ksyms
Source4:	find-provides.ksyms
Source5:	kmodtool
Source6:	symbols.greylist-x86_64
Source7:	preamble

%{!?kmodtool: %define kmodtool %{SOURCE5}}
%define __find_requires %_sourcedir/find-requires.ksyms
%define __find_provides %_sourcedir/find-provides.ksyms %{kmod_name} %{?epoch:%{epoch}:}%{version}-%{release}

Name:		%{kmod_name}
Version:	%{kmod_driver_version}
Release:	%{kmod_rpm_release}%{?dist}.8
Summary:	%{kmod_name} kernel module

Group:		System/Kernel
License:	GPLv2
URL:		https://github.com/amzn/amzn-drivers
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildRequires:	%kernel_module_package_buildreqs
ExclusiveArch:  x86_64


# Build only for standard kernel variant(s); for debug packages, append "debug"
# after "default" (separated by space)
%kernel_module_package -s %{SOURCE5} -f %{SOURCE1} -p %{SOURCE7} default

%description
%{kmod_name} - driver

%prep
%setup

set -- *
mkdir source
mv "$@" source/
cp %{SOURCE6} source/
mkdir obj

%build
echo "Building for kernel: %{kernel_version} flavors: '%{flavors_to_build}'"
echo "Build var: kmodtool = %{kmodtool}"
echo "Build var: kverrel = %{kverrel}"
for flavor in %flavors_to_build; do
	rm -rf obj/$flavor
	cp -r source obj/$flavor

	# update symvers file if existing
	symvers=source/Module.symvers-%{_target_cpu}
	if [ -e $symvers ]; then
		cp $symvers obj/$flavor/%{kmod_kbuild_dir}/Module.symvers
	fi

	make -C %{kernel_source $flavor} M=$PWD/obj/$flavor/%{kmod_kbuild_dir} \
		NOSTDINC_FLAGS="-I $PWD/obj/$flavor/include"

	# mark modules executable so that strip-to-file can strip them
	find obj/$flavor/%{kmod_kbuild_dir} -name "*.ko" -type f -exec chmod u+x '{}' +
done

%{SOURCE2} %{name} %{kmod_kernel_version} obj > source/depmod.conf

greylist=source/symbols.greylist-%{_target_cpu}
if [ -f $greylist ]; then
	cp $greylist source/symbols.greylist
else
	touch source/symbols.greylist
fi

%install
export INSTALL_MOD_PATH=$RPM_BUILD_ROOT
export INSTALL_MOD_DIR=extra/%{name}
for flavor in %flavors_to_build ; do
	make -C %{kernel_source $flavor} modules_install \
		M=$PWD/obj/$flavor/%{kmod_kbuild_dir}
	# Cleanup unnecessary kernel-generated module dependency files.
	find $INSTALL_MOD_PATH/lib/modules -iname 'modules.*' -exec rm {} \;
done

install -m 644 -D source/depmod.conf $RPM_BUILD_ROOT/etc/depmod.d/%{kmod_name}.conf
install -m 644 -D source/symbols.greylist $RPM_BUILD_ROOT/usr/share/doc/kmod-%{kmod_name}/greylist.txt

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Jan 19 2018 vonnyfly - 1.1.5-1%{?dist}
- initial build for RHEL7
