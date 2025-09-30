"""Tests for data models."""

import pytest

from stackbrew_generator.models import RedisVersion, Distribution, DistroType, Release, StackbrewEntry


class TestRedisVersion:
    """Tests for RedisVersion model."""

    def test_parse_basic_version(self):
        """Test parsing basic version strings."""
        version = RedisVersion.parse("8.2.1")
        assert version.major == 8
        assert version.minor == 2
        assert version.patch == 1
        assert version.suffix == ""

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        version = RedisVersion.parse("v8.2.1")
        assert version.major == 8
        assert version.minor == 2
        assert version.patch == 1
        assert version.suffix == ""

    def test_parse_version_with_suffix(self):
        """Test parsing version with suffix."""
        version = RedisVersion.parse("8.2.1-m01")
        assert version.major == 8
        assert version.minor == 2
        assert version.patch == 1
        assert version.suffix == "-m01"

    def test_parse_version_without_patch(self):
        """Test parsing version without patch number."""
        version = RedisVersion.parse("8.2")
        assert version.major == 8
        assert version.minor == 2
        assert version.patch is None
        assert version.suffix == ""

    def test_parse_eol_version(self):
        """Test parsing EOL version."""
        version = RedisVersion.parse("7.4.0-eol")
        assert version.major == 7
        assert version.minor == 4
        assert version.patch == 0
        assert version.suffix == "-eol"
        assert version.is_eol is True

    def test_parse_invalid_version(self):
        """Test parsing invalid version strings."""
        with pytest.raises(ValueError):
            RedisVersion.parse("invalid")

        with pytest.raises(ValueError):
            RedisVersion.parse("0.1.0")  # Major version must be >= 1

    def test_is_milestone(self):
        """Test milestone detection."""
        ga_version = RedisVersion.parse("8.2.1")
        milestone_version = RedisVersion.parse("8.2.1-m01")

        assert ga_version.is_milestone is False
        assert milestone_version.is_milestone is True

    def test_mainline_version(self):
        """Test mainline version property."""
        version = RedisVersion.parse("8.2.1-m01")
        assert version.mainline_version == "8.2"

    def test_string_representation(self):
        """Test string representation."""
        version1 = RedisVersion.parse("8.2.1")
        version2 = RedisVersion.parse("8.2.1-m01")
        version3 = RedisVersion.parse("8.2")

        assert str(version1) == "8.2.1"
        assert str(version2) == "8.2.1-m01"
        assert str(version3) == "8.2"

    def test_version_comparison(self):
        """Test version comparison for sorting."""
        v1 = RedisVersion.parse("8.2.1")
        v2 = RedisVersion.parse("8.2.2")
        v3 = RedisVersion.parse("8.2.1-m01")
        v4 = RedisVersion.parse("8.3.0")

        # Test numeric comparison
        assert v1 < v2
        assert v2 < v4

        # Test milestone vs GA (GA comes after milestone)
        assert v3 < v1

        # Test sorting
        versions = [v4, v1, v3, v2]
        sorted_versions = sorted(versions)
        assert sorted_versions == [v3, v1, v2, v4]


class TestDistribution:
    """Tests for Distribution model."""

    def test_from_dockerfile_alpine(self):
        """Test parsing Alpine distribution from Dockerfile."""
        distro = Distribution.from_dockerfile_line("FROM alpine:3.22")
        assert distro.type == DistroType.ALPINE
        assert distro.name == "alpine3.22"

    def test_from_dockerfile_debian(self):
        """Test parsing Debian distribution from Dockerfile."""
        distro = Distribution.from_dockerfile_line("FROM debian:bookworm")
        assert distro.type == DistroType.DEBIAN
        assert distro.name == "bookworm"

    def test_from_dockerfile_debian_slim(self):
        """Test parsing Debian slim distribution from Dockerfile."""
        distro = Distribution.from_dockerfile_line("FROM debian:bookworm-slim")
        assert distro.type == DistroType.DEBIAN
        assert distro.name == "bookworm"

    def test_from_dockerfile_invalid(self):
        """Test parsing invalid Dockerfile lines."""
        with pytest.raises(ValueError):
            Distribution.from_dockerfile_line("INVALID LINE")

        with pytest.raises(ValueError):
            Distribution.from_dockerfile_line("FROM unsupported:latest")

    def test_is_default(self):
        """Test default distribution detection."""
        alpine = Distribution(type=DistroType.ALPINE, name="alpine3.22")
        debian = Distribution(type=DistroType.DEBIAN, name="bookworm")

        assert alpine.is_default is False
        assert debian.is_default is True

    def test_tag_names(self):
        """Test tag name generation."""
        alpine = Distribution(type=DistroType.ALPINE, name="alpine3.22")
        debian = Distribution(type=DistroType.DEBIAN, name="bookworm")

        assert alpine.tag_names == ["alpine", "alpine3.22"]
        assert debian.tag_names == ["bookworm"]


class TestRelease:
    """Tests for Release model."""

    def test_release_creation(self):
        """Test creating a Release instance."""
        version = RedisVersion.parse("8.2.1")
        distribution = Distribution(type=DistroType.DEBIAN, name="bookworm")

        release = Release(
            commit="abc123def456",
            version=version,
            distribution=distribution,
            git_fetch_ref="refs/tags/v8.2.1"
        )

        assert release.commit == "abc123def456"
        assert release.version == version
        assert release.distribution == distribution

    def test_release_string_representation(self):
        """Test Release string representation."""
        version = RedisVersion.parse("8.2.1")
        distribution = Distribution(type=DistroType.DEBIAN, name="bookworm")

        release = Release(
            commit="abc123def456",
            version=version,
            distribution=distribution,
            git_fetch_ref="refs/tags/v8.2.1"
        )

        expected = "abc123de 8.2.1 debian bookworm"
        assert str(release) == expected


class TestStackbrewEntry:
    """Tests for StackbrewEntry model."""

    def test_debian_architectures(self):
        """Test that Debian distributions get the correct architectures."""
        version = RedisVersion.parse("8.2.1")
        distribution = Distribution(type=DistroType.DEBIAN, name="bookworm")

        entry = StackbrewEntry(
            tags=["8.2.1", "latest"],
            commit="abc123def456",
            version=version,
            distribution=distribution,
            git_fetch_ref="refs/tags/v8.2.1"
        )

        expected_architectures = ["amd64", "arm32v5", "arm32v7", "arm64v8", "i386", "mips64le", "ppc64le", "s390x"]
        assert entry.architectures == expected_architectures

    def test_alpine_architectures(self):
        """Test that Alpine distributions get the correct architectures."""
        version = RedisVersion.parse("8.2.1")
        distribution = Distribution(type=DistroType.ALPINE, name="alpine3.22")

        entry = StackbrewEntry(
            tags=["8.2.1-alpine", "alpine"],
            commit="abc123def456",
            version=version,
            distribution=distribution,
            git_fetch_ref="refs/tags/v8.2.1"
        )

        expected_architectures = ["amd64", "arm32v6", "arm32v7", "arm64v8", "i386", "ppc64le", "riscv64", "s390x"]
        assert entry.architectures == expected_architectures

    def test_stackbrew_entry_string_format(self):
        """Test that StackbrewEntry formats correctly with architectures."""
        version = RedisVersion.parse("8.2.1")
        distribution = Distribution(type=DistroType.ALPINE, name="alpine3.22")

        entry = StackbrewEntry(
            tags=["8.2.1-alpine", "alpine"],
            commit="abc123def456",
            version=version,
            distribution=distribution,
            git_fetch_ref="refs/tags/v8.2.1"
        )

        output = str(entry)

        # Check that it contains the expected Alpine architectures
        assert "amd64, arm32v6, arm32v7, arm64v8, i386, ppc64le, riscv64, s390x" in output
        assert "Tags: 8.2.1-alpine, alpine" in output
        assert "GitCommit: abc123def456" in output
        assert "GitFetch: refs/tags/v8.2.1" in output
        assert "Directory: alpine" in output
