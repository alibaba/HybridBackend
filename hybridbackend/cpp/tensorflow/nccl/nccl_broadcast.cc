/* Copyright 2021 Alibaba Group Holding Limited. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#if HYBRIDBACKEND_TENSORFLOW

#include <tensorflow/core/framework/common_shape_fns.h>
#include <tensorflow/core/framework/op_kernel.h>
#include <tensorflow/core/framework/shape_inference.h>

#include <vector>

#include "hybridbackend/cpp/tensorflow/nccl/nccl_comm.h"

namespace tensorflow {
namespace hybridbackend {

#if HYBRIDBACKEND_NCCL

REGISTER_OP("BroadcastWithNcclComm")
    .Output("output: T")
    .Input("handle: resource")
    .Input("input: T")
    .Attr("root_rank: int >= 0 = 0")
    .Attr("T: {int8, uint8, int32, uint32, int64, uint64, half, float, double}")
    .SetShapeFn([](shape_inference::InferenceContext* c) {
      c->set_output(0, c->input(1));
      return Status::OK();
    })
    .SetIsStateful()
    .Doc(R"doc(
Broadcast using a NCCL communicator.

output: A reduced tensor.
handle: Handle of a NCCL communicator.
input: A tensor to reduce.
root_rank: Rank of the broadcast root.
)doc");

#if GOOGLE_CUDA
class BroadcastWithNcclCommOp : public NcclCommAsyncOp {
 public:
  explicit BroadcastWithNcclCommOp(OpKernelConstruction* ctx)
      : NcclCommAsyncOp(ctx) {
    OP_REQUIRES_OK(ctx, ctx->GetAttr("root_rank", &root_rank_));
    OP_REQUIRES(ctx, root_rank_ >= 0,
                errors::InvalidArgument("root_rank should be >= 0"));
  }

  void ComputeAsyncWithComm(NcclComm* comm, OpKernelContext* ctx,
                            DoneCallback done) override {
    OP_REQUIRES_ASYNC(
        ctx, root_rank_ < comm->size(),
        errors::InvalidArgument("root_rank should be within communicator size"),
        done);

    const Tensor* input;
    OP_REQUIRES_OK_ASYNC(ctx, ctx->input("input", &input), done);
    Tensor* output;
    OP_REQUIRES_OK_ASYNC(ctx, ctx->allocate_output(0, input->shape(), &output),
                         done);

    comm->RunAsync(
        [input, output, this, comm, ctx, done]() {
          VLOG(1) << comm->DebugString() << " [" << name() << "] [Broadcast]";
          OP_REQUIRES_OK_ASYNC(ctx, comm->Broadcast(output, *input, root_rank_),
                               done);
        },
        ctx, done);
  }

 private:
  int32 root_rank_;
};

#define REGISTER_KERNEL(TYPE)                             \
  REGISTER_KERNEL_BUILDER(Name("BroadcastWithNcclComm")   \
                              .Device(DEVICE_GPU)         \
                              .TypeConstraint<TYPE>("T"), \
                          BroadcastWithNcclCommOp);
TF_CALL_NCCL_TYPES(REGISTER_KERNEL);
#undef REGISTER_KERNEL
#endif  // GOOGLE_CUDA

#endif

}  // namespace hybridbackend
}  // namespace tensorflow

#endif  // HYBRIDBACKEND_TENSORFLOW
