#!/bin/sh

until wmii "$@"; do
    sleep 1
done
