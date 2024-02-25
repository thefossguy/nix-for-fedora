## START: Set by rpmautospec
## (rpmautospec version 0.3.5)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 6;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

Name:           nix
Version:        2.18.1
Release:        %autorelease
Summary:        Package manager for NixOS

License:        LGPL-2.1
URL:            https://github.com/NixOS/nix
Source0:        https://github.com/NixOS/nix/archive/%{version_no_tilde}/%{name}-%{version_no_tilde}.tar.gz
Source1:        nix.conf
Source2:        registry.json

BuildRequires:  autoconf
BuildRequires:  autoconf-archive
BuildRequires:  automake
BuildRequires:  bison
BuildRequires:  boost-devel
BuildRequires:  brotli-devel
BuildRequires:  curl-devel
BuildRequires:  editline-devel
BuildRequires:  flex
BuildRequires:  gc-devel
BuildRequires:  gcc-c++
BuildRequires:  gmock-devel
BuildRequires:  gtest-devel
BuildRequires:  jq
BuildRequires:  json-devel
BuildRequires:  libarchive-devel
BuildRequires:  libgit2-devel
BuildRequires:  libseccomp-devel
BuildRequires:  libsodium-devel
BuildRequires:  lowdown-devel
BuildRequires:  openssl-devel
BuildRequires:  rapidcheck-devel
BuildRequires:  sqlite-devel
BuildRequires:  systemd-rpm-macros

%ifarch x86_64
BuildRequires:  libcpuid-devel
%endif

# For documentation, not yet used:
# BuildRequires:  graphviz

%description
Nix is a purely functional package manager. This means that it treats packages
like values in purely functional programming languages such as Haskell — they
are built by functions that don’t have side-effects, and they never change after
they have been built. Nix stores packages in the Nix store, usually the
directory /nix/store, where each package has its own unique subdirectory.

%prep
%autosetup

%build
autoreconf -vfi

OPTIONS=(
  # We need to disable tests because 'rapidtest' dependency is missing
  --disable-tests

  # Documentation is available online
  --disable-doc-gen

  # cpuid is used only on x86, even then, it is optional
%ifnarch x86_64
  --disable-cpuid
%endif

  # Those libraries are unversioned, and we don't install the headers,
  # so let's move them out of the public dir.
  --libdir=%{_libdir}/nix
  --libexecdir=%{_libexecdir}
)

%configure "${OPTIONS[@]}"
%make_build

%install
%make_install

# nix config
mkdir -p %{buildroot}/etc/nix
cp %{SOURCE1} %{SOURCE2} %{buildroot}/etc/nix/

# Devel files that we don't want to use
rm -r %{buildroot}%{_includedir}/nix \
      %{buildroot}%{_libdir}/nix/pkgconfig

# Duplicate shell completion files
rm -r %{buildroot}/etc/profile.d

rm %{buildroot}/etc/init/nix-daemon.conf

ln -vfs --relative %{buildroot}$(readlink %{buildroot}%{_libexecdir}/nix/build-remote) \
                                          %{buildroot}%{_libexecdir}/nix/build-remote

%pre
set -x
nix_dirs=(
    '/nix'
    '/nix/var'
    '/nix/var/log'
    '/nix/var/log/nix'
    '/nix/var/log/nix/drvs'
    '/nix/var/nix'
    '/nix/var/nix/daemon-socket'
    '/nix/var/nix/db'
    '/nix/var/nix/gcroots'
    '/nix/var/nix/gcroots/per-user'
    '/nix/var/nix/profiles'
    '/nix/var/nix/profiles/per-user'
    '/nix/var/nix/temproots'
    '/nix/var/nix/userpool'
)
for d in "${nix_dirs[@]}"; do
    if [ ! -d "$d" ]; then
        mkdir -p "$d"
        chmod 755 "$d"
    fi
done

if ! getent group nixbld > /dev/null; then
    groupadd --system --gid 30000 nixbld
fi
# while the nixos.org manual only shows 10 users in the example,
# the Determinate Systems installer creates 32 users
# more users = more concurrent builds
for n in $(seq 1 32); do
    if ! getent passwd "nixbld$n" > /dev/null; then
        useradd \
            --home-dir /var/empty \
            --comment "Nix build user $n" \
            --gid nixbld \
            --groups nixbld \
            --no-user-group \
            --system \
            --shell "$(command -v nologin)" \
            --uid $(( 30000 + $n )) \
            --password '!' \
            "nixbld$n"
    fi
done

shell_dirs=(
    '/etc/zsh'
    '/usr/share/fish/vendor_conf.d'
)
for d in "${shell_dirs[@]}"; do
    if [ ! -d "$d" ]; then
        mkdir -p "$d"
        chmod 755 "$d"
    fi
done
set +x

%post
%systemd_post nix-daemon.socket nix-daemon.service

%preun
set -x
for n in $(seq 1 32); do
    if getent passwd "nixbld$n" > /dev/null; then
        userdel "nixbld$1"
    fi
done
if getent group nixbld > /dev/null; then
    groupdel nixbld
fi
nix_dirs=(
    '/nix/var/nix/userpool'
    '/nix/var/nix/temproots'
    '/nix/var/nix/profiles/per-user'
    '/nix/var/nix/profiles'
    '/nix/var/nix/gcroots/per-user'
    '/nix/var/nix/gcroots'
    '/nix/var/nix/db'
    '/nix/var/nix/daemon-socket'
    '/nix/var/nix'
    '/nix/var/log/nix/drvs'
    '/nix/var/log/nix'
    '/nix/var/log'
    '/nix/var'
    '/nix'
)
for d in "${nix_dirs[@]}"; do
    if [ -d "$d" ]; then
        rm -rf "$d"
    fi
done
set +x
%systemd_preun nix-daemon.socket nix-daemon.service

%postun
%systemd_postun_with_restart nix-daemon.socket nix-daemon.service

%files
/etc/nix/nix.conf
/etc/nix/registry.json
%{_bindir}/nix
%{_bindir}/nix-*
%dir %{_libdir}/nix
%{_libdir}/nix/libnix*.so
%{_libexecdir}/nix/build-remote
%{_datadir}/bash-completion/completions/nix
%{_datadir}/fish/vendor_completions.d/nix.fish
%{_datadir}/zsh/site-functions/*nix
%doc README.md
%license COPYING

# Let's ignore the daemon stuff for now
%_unitdir/nix-daemon.socket
%_unitdir/nix-daemon.service
%_tmpfilesdir/nix-daemon.conf

%changelog
* Tue Nov 07 2023 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 2.18.1-2
- Switch to already-packaged json dependency and add service files

* Wed Nov 01 2023 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 2.18.1-1
- Initial packaging
