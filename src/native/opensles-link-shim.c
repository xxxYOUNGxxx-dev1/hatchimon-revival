/*
 * Copyright (c) 2007-2009 The Khronos Group Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and /or associated documentation files (the "Materials "), to
 * deal in the Materials without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Materials, and to permit persons to whom the Materials are
 * furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Materials.
 *
 * THE MATERIALS ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE MATERIALS OR THE USE OR OTHER DEALINGS IN THE
 * MATERIALS.
 *
 * OpenSLES_IID.c - OpenSL ES version 1.0
 *
 */
typedef struct { unsigned int a; unsigned short b,c,d; unsigned char e[6]; } ID;
static const ID id_ENGINE = { 0x8d97c260, 0xddd4, 0x11db, 0x958f, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_ENGINE = &id_ENGINE;
static const ID id_SEEK = { 0xd43135a0, 0xdddc, 0x11db, 0xb458, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_SEEK = &id_SEEK;
static const ID id_PREFETCHSTATUS = { 0x2a41ee80, 0xddd8, 0x11db, 0xa41f, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_PREFETCHSTATUS = &id_PREFETCHSTATUS;
static const ID id_VOLUME = { 0x09e8ede0, 0xddde, 0x11db, 0xb4f6, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_VOLUME = &id_VOLUME;
static const ID id_PLAY = { 0xef0bd9c0, 0xddd7, 0x11db, 0xbf49, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_PLAY = &id_PLAY;
static const ID id_ANDROIDSIMPLEBUFFERQUEUE = { 0x198e4940, 0xc5d7, 0x11df, 0xa2a6, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_ANDROIDSIMPLEBUFFERQUEUE = &id_ANDROIDSIMPLEBUFFERQUEUE;
static const ID id_NULL = { 0xec7178ec, 0xe5e1, 0x4432, 0xa3f4, { 0x46, 0x57, 0xe6, 0x79, 0x52, 0x10 } };
const ID * const SL_IID_NULL = &id_NULL;
static const ID id_METADATAEXTRACTION = { 0xaa5b1f80, 0xddd6, 0x11db, 0xac8e, { 0x00, 0x02, 0xa5, 0xd5, 0xc5, 0x1b } };
const ID * const SL_IID_METADATAEXTRACTION = &id_METADATAEXTRACTION;
unsigned int slCreateEngine(void **out,unsigned int n,const void *opts,unsigned int count,const void *ids,const void *required) { if(out) *out=0; return 12; }
